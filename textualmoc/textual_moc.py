"""
textual_moc.py — Importable module for the TextualMOC class
No automatic initialization on import.

Quick start:
    from textual_moc import TextualMOC
    tm = TextualMOC()
    tm.add_text_media_image("Hello MOC!", multimedia_url="https://example.com", hips2fits_image="https://example.com/img.jpg")
    tm.save("moc.json")
"""

from __future__ import annotations

import json
import os
import webbrowser
from datetime import datetime

# Dipendenze opzionali: gestite con try/except per evitare side-effects all'import
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
    import healpy as hp  # type: ignore
except Exception:  # pragma: no cover
    hp = None

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
    # langchain community embeddings (Ollama)
    from langchain_community.embeddings import OllamaEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    OllamaEmbeddings = None

__all__ = ["TextualMOC"]


class TextualMOC:
    def __init__(self, moc=None):
        """
        Initialize the TextualMOC class, optionally with a MOC object.

        Parameters:
        moc (MOC, optional): A MOC object to be serialized and modified. Defaults to None.
        """
        self.moc = moc
        # If a MOC object is provided, serialize it to JSON format and store it in moc_data. 
        # Otherwise, initialize moc_data as an empty dictionary.
        self.moc_data = self.moc.serialize(format='json') if moc else {}
        
        self.ipyaladin = None  # Initialize the Aladin viewer as None

    def annotate_cell(self, order, pixel, text):
        """
        Assigns a textual annotation to a specific MOC cell within the JSON data structure.

        This method updates the internal `moc_data` dictionary by adding or extending the
        `"annotated_cells"` section. The annotation is stored under the specified order and pixel.

        Parameters:
            order (int or str): The HEALPix order (depth) of the MOC cell.
            pixel (int): The pixel index within the specified order.
            text (str): The annotation text to associate with the given cell.

        Raises:
            ValueError: If the specified order or pixel does not exist in the current MOC data.
        """
        order = str(order)
        pixel_str = str(pixel)

        # Check if order and pixel exist in moc_data
        if order not in self.moc_data or pixel not in self.moc_data[order]:
            raise ValueError(f"The combination order={order} and pixel={pixel} does not exist in the MOC data.")

        if 'annotated_cells' not in self.moc_data:
            self.moc_data['annotated_cells'] = {}
        if order not in self.moc_data['annotated_cells']:
            self.moc_data['annotated_cells'][order] = {}
        self.moc_data['annotated_cells'][order][pixel_str] = text

    def add_text_media_image(self, text_file_path="", multimedia_url="", hips2fits_image=""):
        """
        Adds custom text, a multimedia link, and an image link to the MOC's JSON representation.
        Reads from a file or fetches content from a URL.

        Parameters:
        text_file_path (str): The file path to read the text from, a URL, or direct text.
        multimedia_url (str): The multimedia URL to be added.
        image (str): The image URL to be added.
        """
        try:
            if isinstance(text_file_path, str):
                if text_file_path.startswith(('http://', 'https://')):
                    # Fetch content from the URL
                    response = requests.get(text_file_path)
                    response.raise_for_status()  # Raise an exception for HTTP errors
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text().strip()
                elif os.path.isfile(text_file_path):
                    # Assume it's a local file path
                    with open(text_file_path, 'r', encoding='utf-8') as file:
                        text = file.read().strip()
                else:
                    # Directly use the provided text as custom text
                    text = text_file_path

                self.moc_data['custom_text'] = text
            else:
                raise ValueError("Invalid text_file_path. Expected a string URL, file path, or direct text.")

            # Validate multimedia URL
            if isinstance(multimedia_url, str) and multimedia_url.startswith(('http://', 'https://')):
                self.moc_data['multimedia'] = multimedia_url
            else:
                print("Invalid multimedia URL provided. URL should start with http:// or https://")

            # Validate image URL
            if isinstance(image, str) and image.startswith(('http://', 'https://')):
                self.moc_data['hips2fits_image'] = hips2fits_image
            else:
                print("Invalid image URL provided. URL should start with http:// or https://")

        except Exception as e:
            print(f"An error occurred while adding text, media, and image: {e}")

    def embedding_from_custom_text(self, embeddings_model='nomic-embed-text'):
        """
        Reads the 'custom_text' key from the loaded text-based MOC, generates embeddings 
        using LangChain with OllamaEmbeddings (default model: 'nomic-embed-text'), 
        and stores the resulting numerical embedding along with the applied model.

        Parameters:
        embeddings_model (str): The name of the Ollama embedding model to use;
        see: https://python.langchain.com/docs/integrations/text_embedding/ollama/
        """
    
        # Check that there is custom text
        if 'custom_text' in self.moc_data:
            custom_text = self.moc_data['custom_text']
        
            # Create the embeddings instance
            embeddings = OllamaEmbeddings(model=embeddings_model)
        
            # Generate the embedding for the text
            embedding_vector = embeddings.embed_query(custom_text)
        
            # Save embedding and model in MOC
            self.moc_data['embedding'] = embedding_vector
            self.moc_data['embedding_model'] = embeddings_model
        
            print("Embedding added to moc_data using the model:", embeddings_model)
        else:
            print("No 'custom_text' found in MOC data.")


    def load_textual_moc(self, file_path):
        """
        Loads a textual MOC.

        Parameters:
        file_path (str): The path to the JSON file containing the textual MOC data.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.moc_data = json.load(file)

            # Load the MOC area from the JSON data
            self.moc = MOC.from_json(self.moc_data)
            print(f"Textual MOC loaded from {file_path}.")

        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: File {file_path} is not a valid JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def plot_moc_area(self):
        if not self.moc:
            print("No MOC data available for plotting.")
            return

        fig = plt.figure(figsize=(10, 10))
        wcs = self.moc.wcs(fig)
        ax = fig.add_subplot(projection=wcs)
        self.moc.fill(ax, wcs, alpha=0.5)
        self.moc.border(ax, wcs, color='black', alpha=0.7)

        annotations = self.moc_data.get("annotated_cells", {})
        for order, pixels_dict in annotations.items():
            nside = 2 ** int(order)
            for pixel_str, label in pixels_dict.items():
                pixel = int(pixel_str)
                theta, phi = hp.pix2ang(nside, pixel, nest=True)
                ra = np.degrees(phi)
                dec = 90 - np.degrees(theta)
                ax.text(ra, dec, label, transform=ax.get_transform('world'), fontsize=8, color='red')

        plt.title("Visualizing MOC Area")
        plt.grid(True)
        plt.show()

    def show_image_value(self):
        """
        Prints the image URL stored in the MOC data as a clickable link.
        """
        image_url = self.moc_data.get('image', 'No image URL available.')
        print(f"Image URL: {image_url}")
        
    def show_media_value(self):
        """
        Prints the multimedia URL stored in the MOC data.
        """
        print(f"Multimedia URL: {self.moc_data.get('multimedia', 'No multimedia URL available.')}")

    def show_metadata_value(self):
        """
        Prints the metadata information such as author, date, and last text update.
        """
        author = self.moc_data.get('author', 'Unknown')
        date = self.moc_data.get('date', 'Unknown')
        last_text_update = self.moc_data.get('last_text_update', 'Never updated')

        print(f"Author: {author}")
        print(f"Date: {date}")
        print(f"Last Text Update: {last_text_update}")

    def show_text_value(self):
        """
        Prints the custom text stored in the MOC data.
        """
        print(f"Custom Text: {self.moc_data.get('custom_text', 'No custom text available.')}")
    
    def render(self, file_path, show_text=True, show_area=True, show_multimedia=True, 
               show_metadata=True, show_image=True, show_embedding=False, plot_embedding=False):
        """
        Loads the MOC from a JSON file and displays the text, multimedia link, MOC area, metadata, and embedding if present.

        Parameters:
        file_path (str): The path to the JSON file to load.
        show_text (bool): If True, prints the text encapsulated in the JSON.
        show_area (bool): If True, displays the MOC using matplotlib.
        show_multimedia (bool): If True, prints the multimedia link encapsulated in the JSON.
        show_metadata (bool): If True, prints the metadata information.
        show_embedding (bool): If True, prints the embedding information if it exists.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.moc_data = json.load(file)

            # Display text and/or multimedia link if requested
            if show_text:
                self.show_text_value()

            if show_image:
                self.show_image_value()

            if show_multimedia:
                self.show_media_value()

            if show_metadata:
                self.show_metadata_value()

            # Display the embedding if requested
            if show_embedding:
                self.show_embedding()

            # Plot the embedding if requested
            if plot_embedding:
                embedding_info = self.moc_data.get('embedding', None)
                if embedding_info:
                    self.plot_embedding(embedding_info)
                else:
                    print("No embedding available to plot.")
                
            # Show the MOC if requested
            if show_area:
                self.plot_moc_area()

        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: File {file_path} is not a valid JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")
            
    def render_ipyaladin(self, aladin_instance=None, color="magenta", alpha=0.8, survey="P/Mellinger/color", fov=5):
        """Visualize the MOC in an Aladin viewer with defined color, transparency, and HiPS and fov"""
        if not self.moc:
            print("No MOC data available to display.")
            return

        if aladin_instance is None:
            if self.ipyaladin is None:
                self.ipyaladin = Aladin(target="Sgr A*", fov=fov, survey=survey)
            display(self.ipyaladin)
            self.ipyaladin.add_moc(self.moc, color=color, alpha=alpha, fill=True,edge=True,adaptativeDisplay=False)
        else:
            aladin_instance.add_moc(self.moc, color=color, alpha=alpha, fill=True, edge=True,adaptativeDisplay=False)

        # Create a widget to display the text and link
        text_area = widgets.Textarea(
            value=self.moc_data.get('custom_text', ''),
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

        # Display the widgets
        display(widgets.VBox([text_area, multimedia_button]))

    def save(self, output_file_path):
        """
        Saves the Textual MOC with custom text, multimedia, and metadata in JSON format to a file.

        Parameters:
        output_file_path (str): The path of the file where the JSON will be saved.
        """
        try:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.moc_data, file, ensure_ascii=False, indent=2)
            print(f"Data successfully saved to {output_file_path}.")
        except Exception as e:
            print(f"An error occurred while saving: {e}")

    def update_metadata(self, author=None, date=None):
        """
        Updates metadata information such as author and date in the MOC's JSON data.

        Parameters:
        author (str): The author name to be added as metadata.
        date (str): The date to be added as metadata. Defaults to current date if not provided.
        """
        if author:
            self.moc_data['author'] = author

        if date:
            self.moc_data['date'] = date
        else:
            self.moc_data['date'] = datetime.now().strftime('%Y-%m-%d')

    def update_text_inline(self, new_text):
        """
        Appends new text to the custom text stored in the MOC data inline.

        Parameters:
        new_text (str): The new text to append to the custom text field.
        """
        if 'custom_text' in self.moc_data:
            self.moc_data['custom_text'] += "\n" + new_text
        else:
            self.moc_data['custom_text'] = new_text

        self.moc_data['last_text_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

