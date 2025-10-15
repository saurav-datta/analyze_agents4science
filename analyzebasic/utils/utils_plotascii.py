import os
from datetime import datetime

class AsciiPlotHelper:
    """
    Lightweight ASCII visualization helper for quick metric comparisons in terminal.
    """

    @staticmethod
    def plot_metric(results, metric_name, scale=50, fill_char="█",
                    savepath=None, filename=None, timestamped=True):
        """
        Plot a horizontal ASCII bar plot for a given metric across papers.
        """
        lines = []
        lines.append(f"\n=== ASCII Plot: {metric_name} ===")

        # Extract metric values
        data = {
            paper: metrics.get(metric_name)
            for paper, metrics in results.items()
            if isinstance(metrics.get(metric_name), (int, float))
        }

        if not data:
            lines.append(f"(No numeric data found for metric '{metric_name}')")
            output = "\n".join(lines)
            print(output)
            return output

        # Normalize for bar length
        max_val = max(data.values())
        if max_val == 0:
            lines.append("(All values are zero)")
            output = "\n".join(lines)
            print(output)
            return output

        # Sort by descending value
        data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))

        # Build bars
        for paper, val in data.items():
            bar_len = int((val / max_val) * scale)
            bar = fill_char * bar_len
            lines.append(f"{paper:<25} | {bar:<{scale}} | {val:.2f}")

        lines.append(f"\nMax value = {max_val:.2f}, scaled to {scale} chars\n")

        output = "\n".join(lines)
        print(output)

        # Handle saving logic
        if savepath:
            # Convert to string and ensure directory exists
            savepath = os.fspath(savepath)
            if timestamped:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                savepath = os.path.join(savepath, timestamp)

            os.makedirs(savepath, exist_ok=True)
            filename = filename or f"{metric_name}_ascii_plot.txt"
            filepath = os.path.join(savepath, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(output)

            print(f"ASCII plot saved to: {filepath}")

        return output
