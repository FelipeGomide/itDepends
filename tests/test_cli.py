from itdepends.cli import parse_repo_name

def test_wrong_repo_name():
    name = "django"

    valid = parse_repo_name(name)

    assert valid == False

def test_correct_repo_name():
    name = "django/django"

    valid = parse_repo_name(name)

    assert valid == True