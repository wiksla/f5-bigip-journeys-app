import pytest

config = """
sys compatibility-level {
    level 2
}
"""


bigdb_option_1 = """
[Dos.ForceSWdos]
default=false
type=enum
enum=|true|false|
realm=common
scf_config=true
display_name=Dos.ForceSWdos
value=false
"""


bigdb_option_2 = """
[Dos.ForceSWdos]
default=false
type=enum
enum=|true|false|
realm=common
scf_config=true
display_name=Dos.ForceSWdos
"""


CONFLICT_NAME = "CompatibilityLevel"


def test_compatibility_lvl(test_compatibility):
    solution_name = "F5_Recommended_CompatibilityLevel_compatibility_lvl_1"
    validation_data = ("1", "true")

    test_compatibility(
        conflict_name=CONFLICT_NAME,
        solution_name=solution_name,
        conf_file=config,
        conf_dat_file=bigdb_option_1,
        validation_data=validation_data,
    )
    test_compatibility(
        conflict_name=CONFLICT_NAME,
        solution_name=solution_name,
        conf_file=config,
        conf_dat_file=bigdb_option_2,
        validation_data=validation_data,
    )

    solution_name = "CompatibilityLevel_compatibility_lvl_0"
    validation_data = ("0", "false")

    test_compatibility(
        conflict_name=CONFLICT_NAME,
        solution_name=solution_name,
        conf_file=config,
        conf_dat_file=bigdb_option_1,
        validation_data=validation_data,
    )


@pytest.fixture
def test_compatibility(test_solution):
    def _test_compatibility(
        conflict_name, solution_name, validation_data, conf_file="", conf_dat_file=""
    ):
        controller = test_solution(
            conflict_name=conflict_name,
            solution_name=solution_name,
            conf_file=conf_file,
            conf_dat_file=conf_dat_file,
        )

        node = controller.config.fields["sys compatibility-level"]
        assert node.fields["level"].value == validation_data[0]
        assert (
            controller.config.bigdb.get(section="Dos.ForceSWdos", option="value")
            == validation_data[1]
        )

    return _test_compatibility
