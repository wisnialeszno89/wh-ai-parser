from types import SimpleNamespace

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.windowhub_form_reader import WindowHubFormReader
from app.agent.perception.windowhub_win32_form_provider import (
    WindowHubWin32FormProvider,
)
from app.agent.perception.screen_scene import ScreenScene


ROOT_HANDLE = 100
DOCUMENT_HANDLE = 200
DOCUMENT_TITLE = "OFR/4001"


def make_observation():
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - OFR/4001",
        ),
        metadata={
            "window_handle": ROOT_HANDLE,
            "window_rect": SimpleNamespace(
                left=50,
                top=30,
                width=1000,
                height=800,
            ),
        },
    )


def native_record(
    handle,
    *,
    title="",
    class_name="Static",
    visible=True,
    bounds=(120, 120, 200, 145),
    client_bounds=None,
    parent_chain=None,
):
    if client_bounds is None:
        client_bounds = bounds
    if parent_chain is None:
        parent_chain = (handle, DOCUMENT_HANDLE, ROOT_HANDLE)
    return {
        "handle": handle,
        "title": title,
        "class_name": class_name,
        "visible": visible,
        "bounds": bounds,
        "client_bounds": client_bounds,
        "parent_chain": parent_chain,
    }


def make_records():
    return (
        native_record(
            DOCUMENT_HANDLE,
            title=DOCUMENT_TITLE,
            class_name="Afx:MDIChild",
            bounds=(100, 80, 900, 700),
            client_bounds=(110, 110, 890, 690),
            parent_chain=(DOCUMENT_HANDLE, ROOT_HANDLE),
        ),
        native_record(
            301,
            title="1230",
            class_name="Edit",
            bounds=(200, 200, 320, 230),
            client_bounds=(202, 202, 318, 228),
        ),
        native_record(
            302,
            title="Biały",
            class_name="ComboBox",
            bounds=(200, 250, 320, 280),
            client_bounds=(202, 252, 318, 278),
        ),
        native_record(
            401,
            title="Szerokość",
            class_name="Static",
            bounds=(125, 200, 190, 230),
            client_bounds=(125, 200, 190, 230),
        ),
        native_record(
            402,
            title="Kolor",
            class_name="Static",
            bounds=(125, 250, 190, 280),
            client_bounds=(125, 250, 190, 280),
        ),
    )


def make_provider(records, document_label=DOCUMENT_TITLE):
    return WindowHubWin32FormProvider(
        document_label_resolver=lambda _observation, _root: document_label,
        native_snapshot_factory=lambda _root: tuple(records),
    )


def make_scene(elements):
    return ScreenScene(
        observation=make_observation(),
        elements=tuple(elements),
        metadata={"active_document": DOCUMENT_TITLE},
    )


def test_provider_emits_only_uniquely_labeled_controls_in_selected_document():
    elements = make_provider(make_records()).perceive(make_observation())

    assert [(element.kind, element.label) for element in elements] == [
        ("edit", "Szerokość"),
        ("combobox", "Kolor"),
    ]
    assert [element.metadata["current_value"] for element in elements] == [
        "1230",
        "Biały",
    ]
    assert all(
        element.metadata["document_scope"] == DOCUMENT_TITLE
        for element in elements
    )
    assert all(
        element.metadata["scope_status"] == "active_document"
        for element in elements
    )
    assert all(element.x is not None and element.y is not None for element in elements)


def test_form_reader_can_consume_scoped_native_fields_without_uia_edit_nodes():
    elements = make_provider(make_records()).perceive(make_observation())

    fields = WindowHubFormReader().read_active_document(make_scene(elements))

    assert [(field.control_type, field.label, field.value) for field in fields] == [
        ("edit", "Szerokość", "1230"),
        ("combobox", "Kolor", "Biały"),
    ]


def test_provider_fails_closed_when_active_document_window_title_is_not_unique():
    records = make_records() + (
        native_record(
            201,
            title=DOCUMENT_TITLE,
            class_name="Afx:MDIChild",
            bounds=(100, 80, 900, 700),
            client_bounds=(110, 110, 890, 690),
            parent_chain=(201, ROOT_HANDLE),
        ),
    )

    assert make_provider(records).perceive(make_observation()) == ()


def test_provider_omits_field_when_nearest_label_is_ambiguous():
    records = make_records() + (
        native_record(
            403,
            title="Inna etykieta",
            class_name="Static",
            bounds=(125, 200, 190, 230),
            client_bounds=(125, 200, 190, 230),
        ),
    )

    elements = make_provider(records).perceive(make_observation())

    # The edit field has two equally close labels, so it is excluded.
    # The combo field still has its one unambiguous nearby label.
    assert [(element.kind, element.label) for element in elements] == [
        ("combobox", "Kolor"),
    ]


def test_provider_ignores_controls_outside_resolved_document_ancestry():
    records = make_records() + (
        native_record(
            303,
            title="999",
            class_name="Edit",
            bounds=(400, 350, 520, 380),
            client_bounds=(402, 352, 518, 378),
            parent_chain=(303, ROOT_HANDLE),
        ),
        native_record(
            404,
            title="Obca etykieta",
            class_name="Static",
            bounds=(320, 350, 390, 380),
            client_bounds=(320, 350, 390, 380),
            parent_chain=(404, ROOT_HANDLE),
        ),
    )

    elements = make_provider(records).perceive(make_observation())

    assert len(elements) == 2
    assert all(element.label != "Obca etykieta" for element in elements)


def test_provider_ignores_controls_outside_document_client_bounds():
    records = make_records() + (
        native_record(
            303,
            title="999",
            class_name="Edit",
            bounds=(920, 350, 1020, 380),
            client_bounds=(922, 352, 1018, 378),
        ),
        native_record(
            404,
            title="Pole poza dokumentem",
            class_name="Static",
            bounds=(830, 350, 900, 380),
            client_bounds=(830, 350, 900, 380),
        ),
    )

    elements = make_provider(records).perceive(make_observation())

    assert len(elements) == 2
    assert all(element.label != "Pole poza dokumentem" for element in elements)


def test_provider_returns_nothing_when_selected_document_is_unresolved():
    provider = make_provider(make_records(), document_label=None)

    assert provider.perceive(make_observation()) == ()


def test_provider_never_marks_native_fields_as_interaction_authorized():
    elements = make_provider(make_records()).perceive(make_observation())

    assert elements
    assert all(element.interaction_capability.value == "unknown" for element in elements)


def test_provider_prefers_combobox_over_its_native_edit_child():
    document = native_record(
        DOCUMENT_HANDLE,
        title=DOCUMENT_TITLE,
        class_name="Afx:MDIChild",
        bounds=(100, 80, 900, 700),
        client_bounds=(110, 110, 890, 690),
        parent_chain=(DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    combo = native_record(
        302,
        title="",
        class_name="ComboBox",
        bounds=(200, 250, 360, 280),
        client_bounds=(202, 252, 358, 278),
        parent_chain=(302, DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    edit_child = native_record(
        301,
        title="",
        class_name="Edit",
        bounds=(205, 252, 345, 278),
        client_bounds=(207, 253, 343, 277),
        parent_chain=(301, 302, DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    label = native_record(
        401,
        title="Rodzaj transportu",
        class_name="Static",
        bounds=(125, 250, 190, 280),
        client_bounds=(125, 250, 190, 280),
        parent_chain=(401, DOCUMENT_HANDLE, ROOT_HANDLE),
    )

    elements = make_provider((document, combo, edit_child, label)).perceive(
        make_observation()
    )

    assert len(elements) == 1
    assert elements[0].kind == "combobox"
    assert elements[0].label == "Rodzaj transportu"


def test_provider_does_not_reuse_one_native_label_for_two_fields():
    document = native_record(
        DOCUMENT_HANDLE,
        title=DOCUMENT_TITLE,
        class_name="Afx:MDIChild",
        bounds=(100, 80, 900, 700),
        client_bounds=(110, 110, 890, 690),
        parent_chain=(DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    edit = native_record(
        301,
        title="",
        class_name="Edit",
        bounds=(200, 200, 320, 230),
        client_bounds=(202, 202, 318, 228),
        parent_chain=(301, DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    combo = native_record(
        302,
        title="",
        class_name="ComboBox",
        bounds=(205, 200, 325, 230),
        client_bounds=(207, 202, 323, 228),
        parent_chain=(302, DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    shared_label = native_record(
        401,
        title="Rodzaj transportu",
        class_name="Static",
        bounds=(125, 200, 190, 230),
        client_bounds=(125, 200, 190, 230),
        parent_chain=(401, DOCUMENT_HANDLE, ROOT_HANDLE),
    )

    elements = make_provider((document, edit, combo, shared_label)).perceive(
        make_observation()
    )

    # One static HWND cannot independently identify two different fields.
    assert elements == ()


def test_provider_does_not_use_main_window_as_shared_label_container():
    document = native_record(
        DOCUMENT_HANDLE,
        title=DOCUMENT_TITLE,
        class_name="Afx:MDIChild",
        bounds=(100, 80, 900, 700),
        client_bounds=(110, 110, 890, 690),
        parent_chain=(DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    field = native_record(
        301,
        title="",
        class_name="Edit",
        bounds=(200, 200, 320, 230),
        client_bounds=(202, 202, 318, 228),
        # The edit has no shared container with the label before the
        # selected document HWND; sharing only the app root is insufficient.
        parent_chain=(301, 500, DOCUMENT_HANDLE, ROOT_HANDLE),
    )
    label = native_record(
        401,
        title="Szerokość",
        class_name="Static",
        bounds=(125, 200, 190, 230),
        client_bounds=(125, 200, 190, 230),
        parent_chain=(401, 600, DOCUMENT_HANDLE, ROOT_HANDLE),
    )

    elements = make_provider((document, field, label)).perceive(make_observation())

    assert elements == ()
