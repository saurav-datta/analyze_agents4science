import json
import os
from pathlib import Path

from analyzebasic.utils.utils_display import DisplayHelper
from analyzebasic.utils.utils_plotascii import AsciiPlotHelper
from analyzebasic.utils.utils_analyzer import PaperAnalyzer

def load_papers(papers_file_name='papers.json'):
    # Read papers to parse
    current_file_path = Path(__file__).resolve()
    parent_dir = current_file_path.parents[1]
    papers_file_path = parent_dir.joinpath('resources',papers_file_name)
    print(f"Path object of PAPERS_FILE: {papers_file_path}")
    if os.path.exists(papers_file_path):
        with open(papers_file_path, "r", encoding="utf-8") as f:
            papers = json.load(f)
        print(f"Loaded {len(papers)} papers from {papers_file_path}")
    else:
        print(f"File {papers_file_path} not found — using empty paper set.")
        papers = {}
    return papers

def get_figures_dir():
    current_file_path = Path(__file__).resolve()
    parent_dir = current_file_path.parents[1]
    figures_dir = parent_dir.joinpath('outputs','figures')

    return figures_dir

def main():
    # agents4science 2025 guideline:
    # submissions must be no more than 8 pages, excluding references and required statements.
    AIGEN_PAGE_LIMIT = 80  # Use large value to not restrict
    PAPERS_FILE = "papers.json"
    FIGURES_DIR = get_figures_dir()

    papers = load_papers(papers_file_name=PAPERS_FILE)

    # start analyzing
    analyzer = PaperAnalyzer(aigen_page_limit=AIGEN_PAGE_LIMIT)
    results = analyzer.compare_papers(papers)
    results_common = results['base']
    results_we = results['we_stats']

    FLAG_DISPLAY_ASCII_ALL = True
    FLAG_DISPLAY_TABLE_ALL = True
    FLAG_DISPLAY_TABLE_WE_COUNT = True

    if FLAG_DISPLAY_ASCII_ALL:
        # Ascii bar plot
        AsciiPlotHelper.plot_metric(results_common, metric_name="page_count", savepath=FIGURES_DIR,
                                    filename='page_count.txt',
                                    timestamped=False)
        AsciiPlotHelper.plot_metric(results_we, "we_count_per_page_avg", savepath=FIGURES_DIR,
                                    filename='we_count_per_page_avg.txt',
                                    timestamped=False)

    if FLAG_DISPLAY_TABLE_ALL:
        DisplayHelper.display_results(
            results_common,
            papers,
            title="Base metrics",
            metrics_to_display=['page_count']
        )

    if FLAG_DISPLAY_TABLE_WE_COUNT:
        DisplayHelper.display_results(
            results_we,
            papers,
            title="'We' metrics",
            metrics_to_exclude=['we_count_per_page']
        )

if __name__ == '__main__':
    main()