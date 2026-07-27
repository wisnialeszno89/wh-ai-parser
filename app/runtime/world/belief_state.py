from dataclasses import dataclass


@dataclass(slots=True)
class BeliefState:

    #
    # Agent może wykonywać akcje.
    #

    can_execute_actions: bool = False

    #
    # Aktualny tryb pracy.
    #

    frame_mode_active: bool = False

    #
    # Czy interakcja jest zablokowana.
    #

    interaction_blocked: bool = False

    #
    # Czy wykryto błąd.
    #

    error_detected: bool = False