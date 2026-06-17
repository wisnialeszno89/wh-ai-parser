FUNCTION_REGISTRY = {

    "create_construction": {

        "gui_function":
            "Nowa konstrukcja"
    },

    "set_profile": {

        "gui_function":
            "Profile"
    },

    "set_glass": {

        "gui_function":
            "Szyby"
    },

    "set_hardware": {

        "gui_function":
            "Okucia"
    },

    "set_filling": {

        "gui_function":
            "Wypełnienia"
    },

    "set_shutter": {

        "gui_function":
            "Rolety"
    },

    "set_window_sill": {

        "gui_function":
            "Parapety"
    }
}


def get_gui_function(
    action_name: str
):

    return FUNCTION_REGISTRY.get(
        action_name
    )