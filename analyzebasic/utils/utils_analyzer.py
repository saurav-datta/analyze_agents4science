import re
import statistics
from io import BytesIO

import PyPDF2
import requests
from tqdm import tqdm

class PaperAnalyzer:
    def __init__(self, aigen_page_limit):
        self.aigen_page_limit = aigen_page_limit
        self.hedging_words = ['may', 'might', 'could', 'possibly', 'perhaps',
                              'appears', 'suggests', 'seems', 'likely', 'potentially']
        self.transition_phrases = ['furthermore', 'moreover', 'however', 'therefore',
                                   'consequently', 'thus', 'hence', 'accordingly',
                                   'draws on', 'paves the way', 'taken together']

    def fetch_paper(self, url):
        """Fetch PDF from URL or arxiv ID"""
        if 'arxiv.org' in url and 'pdf' not in url:
            # Convert arxiv abstract URL to PDF
            arxiv_id = url.split('/')[-1]
            url = f'https://arxiv.org/pdf/{arxiv_id}.pdf'

        response = requests.get(url)
        return BytesIO(response.content)

    def extract_text(self, pdf_file, max_pages=None):
        """Extract text from PDF and count pages"""
        reader = PyPDF2.PdfReader(pdf_file)
        page_texts = []
        total_pages = len(reader.pages)
        limit = min(max_pages or total_pages, total_pages)

        for i in range(limit):
            page_texts.append(reader.pages[i].extract_text())

        self.page_count = limit  # Store page count
        self.page_texts = page_texts  # Keep each page's text
        return "\n".join(page_texts)

    def _calculate_we_stats(self, text):
        """
        Calculate all 'we'-related statistics separately.
        """
        we_pattern = r'\bwe\b'
        we_stats = {}

        # Compute per-page counts
        we_per_page = {}
        for i, page_text in enumerate(getattr(self, 'page_texts', []), start=1):
            we_per_page[i] = len(re.findall(we_pattern, page_text.lower()))
        we_stats['we_count_per_page'] = we_per_page

        # Compute aggregate stats
        total_we = sum(we_per_page.values())
        we_stats['we_count_total'] = total_we

        we_values = list(we_per_page.values())
        positive_values = [v for v in we_values if v > 0]
        if positive_values:
            we_stats['we_count_per_page_min'] = min(positive_values)
        else:
            we_stats['we_count_per_page_min'] = 0

        if we_values:
            we_stats['we_count_per_page_max'] = max(we_values)
            we_stats['we_count_per_page_avg'] = round(sum(we_values) / len(we_values), 2)
        else:
            we_stats['we_count_per_page_max'] = 0
            we_stats['we_count_per_page_avg'] = 0

        # Word-normalized frequency
        words = re.findall(r'\b\w+\b', text.lower())
        we_stats['we_per_1000'] = (total_we / len(words)) * 1000 if words else 0

        return we_stats

    def calculate_metrics(self, text):
        """Calculate all metrics"""
        metrics = {}

        # Add page count metric
        metrics['page_count'] = getattr(self, 'page_count', 0)

        # Clean text for analysis
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        sentences = re.split(r'[.!?]+', text)

        # Split by double line breaks OR by long gaps between sentences
        paragraphs = []
        current_para = []
        for sent in sentences:
            if len(sent.strip()) > 0:
                if '\n\n' in sent or (current_para and len(current_para) > 3):
                    if current_para:
                        paragraphs.append(' '.join(current_para))
                    current_para = [sent.strip()]
                else:
                    current_para.append(sent.strip())
        if current_para:
            paragraphs.append(' '.join(current_para))

        # Hedging density
        hedging_count = sum(1 for word in words if word in self.hedging_words)
        metrics['hedging_per_100'] = (hedging_count / len(words)) * 100 if words else 0

        # Sections (look for numbered headers)
        section_pattern = r'^\d+\.?\s+[A-Z][a-z]+|^[A-Z][A-Z\s]+$'
        sections = re.findall(section_pattern, text, re.MULTILINE)
        metrics['section_count'] = len(sections)

        # References/Citations - be specific to avoid false positives
        citation_patterns = [
            r'\[\d+\]',  # [1] style
            r'\[[\d,\s-]+\]',  # [1,2,3] or [1-3] style
            r'\([A-Za-z]+\s+et\s+al\.\,?\s+\d{4}\)',  # (Author et al., 2024)
            r'\([A-Za-z]+\s+and\s+[A-Za-z]+\,?\s+\d{4}\)',  # (Author and Author, 2024)
            r'\([A-Za-z]+\,?\s+\d{4}\)',  # (Author, 2024)
            r'[A-Z][a-z]+\s+et\s+al\.\s+\(\d{4}\)',  # Author et al. (2024) - no brackets around whole thing
            r'[A-Z][a-z]+\s+et\s+al\.',  # Author et al. - inline citation without year
            r'[A-Z][a-z]+\s+and\s+[A-Z][a-z]+\s+\(\d{4}\)',  # Author and Author (2024)
        ]

        citations = []
        for pattern in citation_patterns:
            citations.extend(re.findall(pattern, text))
        metrics['citation_count'] = len(set(citations))

        # Better reference counting - look for numbered or bulleted entries
        ref_patterns = [
            r'References?\s*\n(.*?)(?:\n\n[A-Z]|\Z)',
            r'REFERENCES?\s*\n(.*?)(?:\n\n[A-Z]|\Z)',
            r'Bibliography\s*\n(.*?)(?:\n\n[A-Z]|\Z)',
            r'Works Cited\s*\n(.*?)(?:\n\n[A-Z]|\Z)'
        ]

        ref_section = None
        for pattern in ref_patterns:
            ref_section = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if ref_section:
                break

        if ref_section:
            ref_text = ref_section.group(1)
            # Count entries that look like actual references
            ref_entries = []
            lines = ref_text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # Check if line starts a new reference
                if (re.match(r'^\[\d+\]', line) or  # [1] format
                        re.match(r'^\d+\.', line) or  # 1. format
                        re.match(r'^[A-Z][a-z]+,?\s+[A-Z]', line) or  # Author, F. format
                        re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line)):  # First Last format
                    # Additional check: must contain a year (1900-2099) to be a real reference
                    if re.search(r'\b(?:19|20)\d{2}\b', line) or (
                            i + 1 < len(lines) and re.search(r'\b(?:19|20)\d{2}\b', lines[i + 1])):
                        ref_entries.append(line)
            metrics['reference_count'] = len(ref_entries)
        else:
            # Fallback: count unique citations as proxy
            metrics['reference_count'] = metrics['citation_count']

        # Paragraph variance with proper word counts
        para_lengths = [len(p.split()) for p in paragraphs if len(p.split()) > 10]
        if para_lengths and len(para_lengths) > 1:
            metrics['paragraph_length_std'] = statistics.stdev(para_lengths)
            metrics['paragraph_length_mean'] = statistics.mean(para_lengths)
        else:
            metrics['paragraph_length_std'] = 0
            metrics['paragraph_length_mean'] = sum(para_lengths) / len(para_lengths) if para_lengths else 0

        # Decimal precision in numbers
        decimals = re.findall(r'\d+\.\d+', text)
        if decimals:
            precisions = [len(d.split('.')[1]) for d in decimals]
            metrics['avg_decimal_places'] = statistics.mean(precisions)
        else:
            metrics['avg_decimal_places'] = 0

        # Round numbers (%, ×, multiples of 5)
        numbers = re.findall(r'\d+\.?\d*%|\d+×|\d+x|factor of \d+', text)
        round_count = sum(1 for n in numbers if any(x in n for x in ['0%', '5%', '×', 'x']))
        metrics['round_number_ratio'] = round_count / max(len(numbers), 1)

        # Transition phrase density
        trans_count = sum(1 for phrase in self.transition_phrases
                          if phrase in text_lower)
        metrics['transitions_per_page'] = (trans_count / max(len(text) / 3000, 1))

        # Contribution lists (look for (i), (ii), (iii) pattern)
        contrib_pattern = r'\(i+\)|\([a-z]\)|\(\d\)'
        contributions = re.findall(contrib_pattern, text_lower)
        metrics['contribution_list_items'] = len(contributions)

        # More flexible abstract detection
        abstract_patterns = [
            r'abstract[:\s]*(.*?)(?:introduction|keywords|1\s+introduction|\n1\.)',
            r'ABSTRACT[:\s]*(.*?)(?:INTRODUCTION|Keywords|1\s+INTRODUCTION|\n1\.)',
            r'Summary[:\s]*(.*?)(?:introduction|1\s+introduction|\n1\.)'
        ]

        abstract_found = False
        for pattern in abstract_patterns:
            abstract_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if abstract_match:
                abstract_words = len(abstract_match.group(1).split())
                metrics['abstract_word_count'] = abstract_words
                abstract_found = True
                break

        if not abstract_found:
            metrics['abstract_word_count'] = 0  # Use 0 instead of NaN

        # Sentence length variance
        sentence_lengths = [len(s.split()) for s in sentences if len(s.split()) > 3]
        if sentence_lengths and len(sentence_lengths) > 1:
            metrics['sentence_length_std'] = statistics.stdev(sentence_lengths)
        else:
            metrics['sentence_length_std'] = 0

        return metrics

    def analyze_paper(self, url, max_pages=None):
        """Main analysis function"""
        pdf_file = self.fetch_paper(url)
        text = self.extract_text(pdf_file, max_pages=max_pages)
        metrics = self.calculate_metrics(text)
        we_stats = self._calculate_we_stats(text)

        return {
            "base": metrics,
            "we_stats": we_stats
        }

    def compare_papers(self, papers):
        """
        Compare multiple papers.
        """
        results = {"base": {}, "we_stats": {}}
        for name, info in tqdm(papers.items(), desc="Analyzing Papers", unit="paper"):
            url = info.get("url")
            paper_type = info.get("type")
            max_pages = None
            if paper_type == 'AIGen':
                max_pages = self.aigen_page_limit

            analysis = self.analyze_paper(url, max_pages=max_pages)

            results["base"][name] = analysis["base"]
            results["we_stats"][name] = analysis["we_stats"]

        return results

