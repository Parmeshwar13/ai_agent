from core.text import project_key, unique_key, unique_slug


def test_unique_slug_adds_a_suffix():
    taken = {"atlas", "atlas-2"}

    def exists(candidate):
        return candidate in taken

    assert unique_slug("Atlas", exists, fallback="project") == "atlas-3"
    assert unique_slug("!!!", exists, fallback="project") == "project"


def test_project_key_uses_initials_and_avoids_collisions():
    assert project_key("Workforce management") == "WM"
    assert project_key("Clinic") == "CLIN"
    assert unique_key("Workforce management", lambda candidate: candidate == "WM") == "WM2"
