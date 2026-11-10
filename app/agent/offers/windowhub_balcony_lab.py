"""Build a single tilt-turn balcony sash with an explicit simulated threshold."""

from app.agent.offers.windowhub_single_sash_lab import simulate_single_tilt_turn


def simulate_balcony_window(row):
    threshold = row.get("threshold")
    if threshold not in ("standard", "low"):
        raise ValueError("Potwierdź typ progu balkonowego: standardowy albo niski.")
    if row.get("single_sash_confirmed") is not True or row.get("swing") != "inward":
        raise ValueError("Potwierdź jedno skrzydło balkonowe otwierane do wewnątrz.")
    return simulate_single_tilt_turn(row, threshold=threshold)
