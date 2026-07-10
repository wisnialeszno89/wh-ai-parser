from dataclasses import dataclass, field


@dataclass(slots=True)
class BeliefState:

    frame_selected: bool = False

    toolbar_visible: bool = False

    popup_visible: bool = False

    beliefs: dict[str, bool] = field(default_factory=dict)

    def set(self, name: str, value: bool = True):

        self.beliefs[name] = value

    def get(self, name: str) -> bool:

        return self.beliefs.get(name, False)