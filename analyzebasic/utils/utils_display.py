import pandas as pd

class DisplayHelper:
    """
    Handles display, formatting, and grouping of analysis results.
    """

    @staticmethod
    def format_comparison_table(results, metrics_to_display=None, metrics_to_exclude=None):
        """Format results as a table with papers as columns and metrics as rows."""

        df = pd.DataFrame(results)

        # Optional filtering
        if metrics_to_display:
            df = df[df.index.isin(metrics_to_display)]
        elif metrics_to_exclude:
            df = df[~df.index.isin(metrics_to_exclude)]

        df = df.sort_index()
        pd.options.display.float_format = '{:.2f}'.format
        return df

    @staticmethod
    def _group_papers_by_key(papers, key):
        """Helper: group paper names by a metadata key (e.g., 'type', 'year')."""
        groups = {}
        for name, info in papers.items():
            group_value = info.get(key, "Unknown")
            groups.setdefault(group_value, []).append(name)
        return groups

    @classmethod
    def format_comparison_by_type(cls, results, papers, group_key="type",
                                  metrics_to_display=None, metrics_to_exclude=None):
        """Return grouped DataFrames by paper metadata key (e.g., 'type')."""
        import pandas as pd
        df = pd.DataFrame(results)

        if metrics_to_display:
            df = df[df.index.isin(metrics_to_display)]
        elif metrics_to_exclude:
            df = df[~df.index.isin(metrics_to_exclude)]

        df = df.sort_index()
        grouped = {}
        groups = cls._group_papers_by_key(papers, group_key)
        for group, names in groups.items():
            cols = [c for c in df.columns if c in names]
            if cols:
                grouped[group] = df[cols]
        return grouped

    @classmethod
    def display_results(cls, results, papers, title="Comparison Table",
                        metrics_to_display=None, metrics_to_exclude=None,
                        group_key="type"):
        """
        Generic display utility for analysis results.
        """
        # Overall metrics
        df_all = cls.format_comparison_table(results,
                                             metrics_to_display=metrics_to_display,
                                             metrics_to_exclude=metrics_to_exclude)
        print(f"\n=== {title} (Overall) ===")
        print(df_all.to_string())

        print(f"\n=== {title} by {group_key.capitalize()} ===")
        grouped_tables = cls.format_comparison_by_type(
            results,
            papers,
            group_key=group_key,
            metrics_to_display=metrics_to_display,
            metrics_to_exclude=metrics_to_exclude
        )

        for group, df in grouped_tables.items():
            print(f"\n{group} Papers:")
            print(df.to_string())

        return grouped_tables
