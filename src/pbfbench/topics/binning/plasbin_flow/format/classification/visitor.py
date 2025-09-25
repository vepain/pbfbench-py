"""Classification format result visitors."""

"""PlasBin-flow classification result formatting module."""

from typing import final

import pbfbench.abc.topic.results as abc_topic_res
import pbfbench.topics.classification.visitor as class_visitor

from . import platon, results


@final
class PlasmidnessVisitor(
    abc_topic_res.FormattedVisitor[class_visitor.Tools, results.Plasmidness],
):
    """Plasmidness result visitor."""

    # TODO[2025-09-24 12:31:12] Mimic as for result visitor (with Error)

    @classmethod
    def convert_fn(
        cls,
        tool: class_visitor.Tools,
    ) -> abc_topic_res.ConvertFn[results.Plasmidness] | abc_topic_res.Error:
        """Get convert function."""

        def _err(tool: class_visitor.Tools) -> abc_topic_res.Error:
            return abc_topic_res.Error(
                "Function to convert classification result to plasmidness result"
                f" is not implemented for `{tool}` ",
            )

        match tool:
            case class_visitor.Tools.PLATON:
                return platon.plasmidness
            case class_visitor.Tools.PLASCLASS:
                return _err(tool)  # FEATURE PlasClass plasmidness convert
            case class_visitor.Tools.PLASGRAPH2:
                return _err(tool)  # FEATURE PlasGraph2 plasmidness convert

    @classmethod
    def result_builder(cls) -> type[results.Plasmidness]:
        """Get result builder."""
        return results.Plasmidness


@final
class SeedsVisitor(abc_topic_res.FormattedVisitor[class_visitor.Tools, results.Seeds]):
    """Seeds result visitor."""

    @classmethod
    def convert_fn(
        cls,
        tool: class_visitor.Tools,
    ) -> abc_topic_res.ConvertFn[results.Seeds] | abc_topic_res.Error:
        """Get convert function."""

        def _err(tool: class_visitor.Tools) -> abc_topic_res.Error:
            return abc_topic_res.Error(
                "Function to convert classification result to plasmidness result"
                f" is not implemented for `{tool}` ",
            )

        match tool:
            case class_visitor.Tools.PLATON:
                return platon.seeds
            case class_visitor.Tools.PLASCLASS:
                return _err(tool)  # FEATURE PlasClass seeds convert
            case class_visitor.Tools.PLASGRAPH2:
                return _err(tool)  # FEATURE PlasGraph2 seeds convert

    @classmethod
    def result_builder(cls) -> type[results.Seeds]:
        """Get result builder."""
        return results.Seeds
