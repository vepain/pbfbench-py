"""Sample items."""


class Item:
    """Sample item."""

    def __init__(self, species_id: str, sample_id: str) -> None:
        """Initialize."""
        self.__species_id = species_id
        self.__sample_id = sample_id

    def species_id(self) -> str:
        """Get species id."""
        return self.__species_id

    def sample_id(self) -> str:
        """Get sample id."""
        return self.__sample_id

    def exp_sample_id(self) -> str:
        """Get experiment sample ID."""
        return fmt_exp_sample_id(self.__species_id, self.__sample_id)


def fmt_exp_sample_id(species_id: str, sample_id: str) -> str:
    """Get species-sample ID directory name.

    * `species_id` can be directly the species ID or a variable name.
    * `sample_id` can be directly the sample ID or a variable name.
    """
    return f"{species_id}_{sample_id}"
