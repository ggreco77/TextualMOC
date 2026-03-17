"""
enriched_moc.py — TextualMOC and SemanticMOC classes.

Quick start:
    # Tutorial 1 — only text
    from enriched_moc import TextualMOC
    tm = TextualMOC(moc)
    tm.add_text_media_image("Hello MOC!", multimedia_url="https://example.com", image="https://example.com/img.jpg")
    tm.save("moc.json")

    # Tutorial 2 — text + embedding
    from enriched_moc import SemanticMOC
    sm = SemanticMOC(moc)
    sm.add_text_media_image("Hello MOC!", multimedia_url="https://example.com")
    sm.embedding_from_custom_text()
    sm.save("semantic_moc.json")
"""

from __future__ import annotations

import json
import os
import webbrowser
from datetime import datetime

# Optional dependencies
try:
    import requests
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    requests = None
    BeautifulSoup = None

try:
    import matplotlib.pyplot as plt  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    plt = None
    np = None

try:
    from cdshealpix.nested import healpix_to_lonlat  # type: ignore
    import astropy.units as u  # type: ignore
except Exception:  # pragma: no cover
    healpix_to_lonlat = None
    u = None

try:
    from mocpy import MOC  # type: ignore
except Exception:  # pragma: no cover
    MOC = None

try:
    from ipyaladin import Aladin  # type: ignore
    import ipywidgets as widgets  # type: ignore
    from IPython.display import display  # type: ignore
except Exception:  # pragma: no cover
    Aladin = None
    widgets = None
    display = None

try:
    from langchain_community.embeddings import OllamaEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    OllamaEmbeddings = None

__all__ = ["TextualMOC", "SemanticMOC"]
__version__ = "0.0.7"


# ════════════════════════════════════════════════════════════════════════
#  TextualMOC — MOC + text, media, annotations, metadata, plotting
# ════════════════════════════════════════════════════════════════════════

class TextualMOC:
    """
    Enhances a MOC (Multi-Order Coverage) with textual content,
    multimedia links, images, metadata, and cell annotations.
    """

    def __init__(self, moc=None):
        """
        Initialize the TextualMOC class, optionally with a MOC object.

        Parameters:
            moc (MOC, optional): A MOC object to be serialized and modified.
        """
        self.moc = moc
        self.moc_data = self.moc.serialize(format='json') if moc else {}
        self.ipyaladin = None

    # ── Text, Media, Image ──────────────────────────────────────────────

    def add_text_media_image(self, text_file_path="", multimedia_url="", image=""):
        """
        Adds custom text, a multimedia link, and an image link to the MOC's
        JSON representation. Reads from a file, URL, or direct text.

        Parameters:
            text_file_path (str): File path, URL, or direct text.
            multimedia_url (str): Multimedia URL to add.
            image (str): Image URL to add.
        """
        try:
            if isinstance(text_file_path, str):
                if text_file_path.startswith(('http://', 'https://')):
                    response = requests.get(text_file_path)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text().strip()
                elif os.path.isfile(text_file_path):
                    with open(text_file_path, 'r', encoding='utf-8') as file:
                        text = file.read().strip()
                else:
                    text = text_file_path

                self.moc_data['text'] = text
            else:
                raise ValueError("Invalid text_file_path. Expected a string URL, file path, or direct text.")

            if isinstance(multimedia_url, str) and multimedia_url.startswith(('http://', 'https://')):
                self.moc_data['multimedia'] = multimedia_url
            elif multimedia_url:
                print("Invalid multimedia URL provided. URL should start with http:// or https://")

            if isinstance(image, str) and image.startswith(('http://', 'https://')):
                self.moc_data['image'] = image
            elif image:
                print("Invalid image URL provided. URL should start with http:// or https://")

        except Exception as e:
            print(f"An error occurred while adding text, media, and image: {e}")

    def update_text_inline(self, new_text):
        """
        Appends new text to the custom text stored in the MOC data.

        Parameters:
            new_text (str): Text to append.
        """
        if 'text' in self.moc_data:
            self.moc_data['text'] += "\n" + new_text
        else:
            self.moc_data['text'] = new_text

        self.moc_data['last_text_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # ── Cell Annotation ─────────────────────────────────────────────────

    def annotate_cell(self, order, pixel, text):
        """
        Assigns a textual annotation to a specific MOC cell.

        Parameters:
            order (int or str): HEALPix order (depth).
            pixel (int): Pixel index within the specified order.
            text (str): Annotation text.

        Raises:
            ValueError: If order/pixel does not exist in current MOC data.
        """
        order = str(order)
        pixel_str = str(pixel)

        if order not in self.moc_data or pixel not in self.moc_data[order]:
            raise ValueError(
                f"The combination order={order} and pixel={pixel} "
                f"does not exist in the MOC data."
            )

        if 'annotated_cells' not in self.moc_data:
            self.moc_data['annotated_cells'] = {}
        if order not in self.moc_data['annotated_cells']:
            self.moc_data['annotated_cells'][order] = {}
        self.moc_data['annotated_cells'][order][pixel_str] = text

    # ── Metadata ────────────────────────────────────────────────────────

    def update_metadata(self, author=None, date=None):
        """
        Updates metadata such as author and date.

        Parameters:
            author (str, optional): Author name.
            date (str, optional): Date string. Defaults to current date.
        """
        if author:
            self.moc_data['author'] = author
        if date:
            self.moc_data['date'] = date
        else:
            self.moc_data['date'] = datetime.now().strftime('%Y-%m-%d')

    # ── Show Methods ────────────────────────────────────────────────────

    def show_text_value(self):
        """Prints the custom text stored in the MOC data."""
        print(f"Custom Text: {self.moc_data.get('text', 'No custom text available.')}")

    def show_image_value(self):
        """Prints the image URL stored in the MOC data."""
        print(f"Image URL: {self.moc_data.get('image', 'No image URL available.')}")

    def show_media_value(self):
        """Prints the multimedia URL stored in the MOC data."""
        print(f"Multimedia URL: {self.moc_data.get('multimedia', 'No multimedia URL available.')}")

    def show_metadata_value(self):
        """Prints metadata: author, date, and last text update."""
        print(f"Author: {self.moc_data.get('author', 'Unknown')}")
        print(f"Date: {self.moc_data.get('date', 'Unknown')}")
        print(f"Last Text Update: {self.moc_data.get('last_text_update', 'Never updated')}")

    # ── Plotting ────────────────────────────────────────────────────────

    def plot_moc_area(self, moc_color="royalblue", moc_alpha=0.3,
                      annotation_fill_color="red", annotation_fill_alpha=0.7,
                      annotation_border_color="darkred"):
        """
        Visualizes the MOC area using matplotlib. Annotated cells are
        highlighted as filled regions with a different color.

        Parameters:
            moc_color (str): Fill color for the main MOC. Default: 'royalblue'.
            moc_alpha (float): Transparency for the main MOC. Default: 0.3.
            annotation_fill_color (str): Fill color for annotated cells. Default: 'red'.
            annotation_fill_alpha (float): Transparency for annotated cells. Default: 0.7.
            annotation_border_color (str): Border color for annotated cells. Default: 'darkred'.
        """
        if not self.moc:
            print("No MOC data available for plotting.")
            return

        fig = plt.figure(figsize=(10, 10))
        wcs = self.moc.wcs(fig)
        ax = fig.add_subplot(projection=wcs)

        # Plot the full MOC
        self.moc.fill(ax, wcs, alpha=moc_alpha, color=moc_color)
        self.moc.border(ax, wcs, color='black', alpha=0.5)

        # Highlight annotated cells as filled regions + text label
        annotations = self.moc_data.get("annotated_cells", {})
        for order, pixels_dict in annotations.items():
            depth = int(order)
            for pixel_str, label in pixels_dict.items():
                pixel = int(pixel_str)

                # Create a mini-MOC from the single annotated cell
                cell_moc = MOC.from_healpix_cells(
                    np.array([pixel]), np.array([depth]), depth
                )
                cell_moc.fill(ax, wcs, alpha=annotation_fill_alpha,
                              color=annotation_fill_color)
                cell_moc.border(ax, wcs, color=annotation_border_color, alpha=0.9)

                # Place the text label at the cell center
                if healpix_to_lonlat is not None:
                    lon, lat = healpix_to_lonlat(np.array([pixel]), depth=depth)
                    ra = lon[0].to_value(u.deg)
                    dec = lat[0].to_value(u.deg)
                    ax.text(ra, dec, label,
                            transform=ax.get_transform('world'),
                            fontsize=8, color='white', fontweight='bold',
                            ha='center', va='center')

        ax.coords.grid(True, color='gray', ls='--', alpha=0.3)
        plt.title("Visualizing MOC Area")
        plt.show()

    # ── Render ──────────────────────────────────────────────────────────

    def render(self, file_path, show_text=True, show_area=True, show_multimedia=True,
               show_metadata=True, show_image=True, show_embedding=False,
               plot_embedding=False):
        """
        Loads the MOC from a JSON file and displays its contents.

        Parameters:
            file_path (str): Path to the JSON file.
            show_text (bool): Print the encapsulated text.
            show_area (bool): Display the MOC area with matplotlib.
            show_multimedia (bool): Print the multimedia link.
            show_metadata (bool): Print metadata.
            show_image (bool): Print image URL.
            show_embedding (bool): Print embedding info (SemanticMOC only).
            plot_embedding (bool): Plot the embedding (SemanticMOC only).
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.moc_data = json.load(file)

            if show_text:
                self.show_text_value()
            if show_image:
                self.show_image_value()
            if show_multimedia:
                self.show_media_value()
            if show_metadata:
                self.show_metadata_value()
            if show_embedding and hasattr(self, 'show_embedding'):
                self.show_embedding()
            if plot_embedding:
                embedding_info = self.moc_data.get('embedding', None)
                if embedding_info and hasattr(self, 'plot_embedding'):
                    self.plot_embedding(embedding_info)
                else:
                    print("No embedding available to plot.")
            if show_area:
                self.plot_moc_area()

        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: File {file_path} is not a valid JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def render_ipyaladin(self, aladin_instance=None, color="magenta", opacity=0.5,
                         survey="P/Mellinger/color", fov=5,
                         annotation_color="red", annotation_opacity=0.8):
        """
        Visualize the MOC in an Aladin viewer. Annotated cells are
        highlighted as separate colored MOC overlays.

        Parameters:
            aladin_instance: Existing Aladin widget to reuse.
            color (str): MOC fill color. Default: 'magenta'.
            opacity (float): MOC transparency (0=invisible, 1=opaque). Default: 0.5.
            survey (str): HiPS survey to display. Default: 'P/Mellinger/color'.
            fov (float): Field of view in degrees. Default: 5.
            annotation_color (str): Color for annotated cell overlay. Default: 'red'.
            annotation_opacity (float): Opacity for annotated cell overlay. Default: 0.8.
        """
        if not self.moc:
            print("No MOC data available to display.")
            return

        if aladin_instance is not None:
            viewer = aladin_instance
        else:
            viewer = Aladin(target="Sgr A*", fov=fov, survey=survey)
            self.ipyaladin = viewer

        display(viewer)
        viewer.add_moc(self.moc, color=color, opacity=opacity,
                       fill=True, edge=True, adaptativeDisplay=False)

        # Highlight annotated cells as separate colored MOC overlays
        annotations = self.moc_data.get("annotated_cells", {})
        for order, pixels_dict in annotations.items():
            depth = int(order)
            for pixel_str, label in pixels_dict.items():
                pixel = int(pixel_str)
                cell_moc = MOC.from_healpix_cells(
                    np.array([pixel]), np.array([depth]), depth
                )
                viewer.add_moc(cell_moc, name=label, color=annotation_color,
                               opacity=annotation_opacity, fill=True, edge=True)

        text_area = widgets.Textarea(
            value=self.moc_data.get('text', ''),
            placeholder='Encapsulated text',
            description='Text:',
            disabled=True,
            layout=widgets.Layout(width='100%', height='200px')
        )

        multimedia_button = widgets.Button(
            description='Open Media',
            button_style='success',
            tooltip='Click to open the multimedia content',
            icon='external-link'
        )

        def open_multimedia(b):
            multimedia_url = self.moc_data.get('multimedia', '')
            if multimedia_url:
                webbrowser.open(multimedia_url)
            else:
                print("No multimedia URL available.")

        multimedia_button.on_click(open_multimedia)
        display(widgets.VBox([text_area, multimedia_button]))

    # ── Load / Save ─────────────────────────────────────────────────────

    def load_textual_moc(self, file_path):
        """
        Loads a Textual MOC from a JSON file.

        Parameters:
            file_path (str): Path to the JSON file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.moc_data = json.load(file)
            self.moc = MOC.from_json(self.moc_data)
            print(f"Textual MOC loaded from {file_path}.")
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: File {file_path} is not a valid JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def save(self, output_file_path):
        """
        Saves the Textual MOC in JSON format.

        Parameters:
            output_file_path (str): Output file path.
        """
        try:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.moc_data, file, ensure_ascii=False, indent=2)
            print(f"Data successfully saved to {output_file_path}.")
        except Exception as e:
            print(f"An error occurred while saving: {e}")


# ════════════════════════════════════════════════════════════════════════
#  SemanticMOC — TextualMOC + vector embeddings
# ════════════════════════════════════════════════════════════════════════

class SemanticMOC(TextualMOC):
    """
    Extends TextualMOC with semantic embedding capabilities.

    Inherits all TextualMOC functionality (text, media, annotations,
    metadata, plotting, Aladin rendering) and adds methods to generate
    and manage vector embeddings from the encapsulated text.
    """

    def __init__(self, moc=None):
        """
        Initialize SemanticMOC.

        Parameters:
            moc (MOC, optional): A MOC object to be serialized and modified.
        """
        super().__init__(moc)

    # ── Embedding ───────────────────────────────────────────────────────

    def embedding_from_custom_text(self, embeddings_model='nomic-embed-text'):
        """
        Generates an embedding from the 'text' key in moc_data using
        LangChain OllamaEmbeddings and stores it in moc_data.

        Parameters:
            embeddings_model (str): Ollama embedding model name.
                See: https://python.langchain.com/docs/integrations/text_embedding/ollama/
        """
        if OllamaEmbeddings is None:
            print("Error: langchain_community is not installed. "
                  "Install it with: pip install langchain-community")
            return

        if 'text' not in self.moc_data:
            print("No 'text' found in MOC data.")
            return

        text = self.moc_data['text']
        embeddings = OllamaEmbeddings(model=embeddings_model)
        embedding_vector = embeddings.embed_query(text)

        self.moc_data['embedding'] = embedding_vector
        self.moc_data['embedding_model'] = embeddings_model

        print("Embedding added to moc_data using the model:", embeddings_model)

    def show_embedding(self):
        """Prints the embedding info stored in the MOC data."""
        embedding = self.moc_data.get('embedding', None)
        model = self.moc_data.get('embedding_model', 'Unknown')

        if embedding:
            print(f"Embedding model: {model}")
            print(f"Embedding dimension: {len(embedding)}")
            print(f"Embedding (first 5 values): {embedding[:5]}")
        else:
            print("No embedding available.")

    def plot_embedding(self, embedding):
        """
        Plots the embedding vector as a bar chart.

        Parameters:
            embedding (list): The embedding vector to plot.
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.bar(range(len(embedding)), embedding, width=1.0, color='steelblue')
            ax.set_xlabel("Dimension")
            ax.set_ylabel("Value")
            ax.set_title(f"Embedding vector ({len(embedding)} dimensions)")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Error plotting embedding: {e}")

    # ── Load ────────────────────────────────────────────────────────────

    def load_semantic_moc(self, file_path):
        """
        Loads a Semantic MOC from a JSON file.
        Calls load_textual_moc and reports embedding status.

        Parameters:
            file_path (str): Path to the JSON file.
        """
        self.load_textual_moc(file_path)

        if 'embedding' in self.moc_data:
            model = self.moc_data.get('embedding_model', 'Unknown')
            dim = len(self.moc_data['embedding'])
            print(f"  └─ Embedding found: model={model}, dimensions={dim}")
        else:
            print("  └─ No embedding found in this file.")
