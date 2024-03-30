import json
import ee
import geemap
import solara
import matplotlib.cm as cm
from matplotlib.colors import rgb2hex
import numpy as np
import ipywidgets as widgets
from pathlib import Path
import sys

# read in the dataset file json

# dataset_path  = "/static/public/dataset.json"
dataset_path = "public/dataset.json"
# colorbar_path = "/static/public/colorbar_r.png"
colorbar_path = "public/colorbar_r.png"


dataset = [
    {
        "uri_to_s1": "",
        "uri_to_s2": "https://storage.googleapis.com/sand_mining_inference/chambal/2023-10-01/S2/chambal_s2_2023-10-01.tif",
        "uri_to_s2_l1c": "",
        "uri_to_prediction": "https://storage.googleapis.com/sand_mining_inference/chambal/2023-10-01/chambal_prediction_2023-10-01.tif",
        "date": "2023-10-01",
        "river": "chambal",
        "uid": "6r8ypwmb",
        "uri_to_river": "https://storage.googleapis.com/sand_mining_inference/chambal/chambal.geojson",
    },
    {
        "uri_to_s1": "",
        "uri_to_s2": "https://storage.googleapis.com/sand_mining_inference/chambal/2023-11-01/S2/chambal_s2_2023-11-01.tif",
        "uri_to_s2_l1c": "",
        "uri_to_prediction": "https://storage.googleapis.com/sand_mining_inference/chambal/2023-11-01/chambal_prediction_2023-11-01.tif",
        "date": "2023-11-01",
        "river": "chambal",
        "uid": "6r8ypwmb",
        "uri_to_river": "https://storage.googleapis.com/sand_mining_inference/chambal/chambal.geojson",
    },
    {
        "uri_to_s1": "",
        "uri_to_s2": "https://storage.googleapis.com/sand_mining_inference/chambal/2023-12-01/S2/chambal_s2_2023-12-01.tif",
        "uri_to_s2_l1c": "",
        "uri_to_prediction": "https://storage.googleapis.com/sand_mining_inference/chambal/2023-12-01/chambal_prediction_2023-12-01.tif",
        "date": "2023-12-01",
        "river": "chambal",
        "uid": "6r8ypwmb",
        "uri_to_river": "https://storage.googleapis.com/sand_mining_inference/chambal/chambal.geojson",
    },
    {
        "uri_to_s1": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-02-01/S1/chambal_s1_2022-02-01.tif",
        "uri_to_s2": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-02-01/S2/chambal_s2_2022-02-01.tif",
        "uri_to_s2_l1c": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-02-01/S2_L1C/chambal_s2l1c_2022-02-01.tif",
        "uri_to_prediction": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-02-01/chambal_prediction_2022-02-01_6r8ypwmb.tif",
        "date": "2022-02-01",
        "river": "chambal",
        "uid": "6r8ypwmb",
        "uri_to_river": "https://storage.googleapis.com/sand_mining_inference/chambal/chambal.geojson",
    },
    {
        "uri_to_s1": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-05-01/S1/chambal_s1_2022-05-01.tif",
        "uri_to_s2": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-05-01/S2/chambal_s2_2022-05-01.tif",
        "uri_to_s2_l1c": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-05-01/S2_L1C/chambal_s2l1c_2022-05-01.tif",
        "uri_to_prediction": "https://storage.googleapis.com/sand_mining_inference/chambal/2022-05-01/chambal_prediction_2022-05-01_6r8ypwmb.tif",
        "date": "2022-05-01",
        "river": "chambal",
        "uid": "6r8ypwmb",
        "uri_to_river": "https://storage.googleapis.com/sand_mining_inference/chambal/chambal.geojson",
    },
]

locations = {}


def replace_gcp_uri(uri: str):
    uri = uri.replace("https://storage.googleapis.com/", "gs://", 1)
    return uri


# iterate over the dataset and create a new id that is a combination of the river name and date, and then use that as the key for every item in the dataset
for item in dataset:
    item["id"] = f"{item['river']}_{item['date']}"
    locations[item["id"]] = item

    # for any key that starts with "uri", replace the uri with a gcp uri
    for key in item.keys():
        if key.startswith("uri"):
            item[key] = replace_gcp_uri(item[key])


zoom = solara.reactive(10)
center = solara.reactive([40, -100])

wandb_id = "6r8ypwmb"
threshold = 0.01

# Generate a magma colormap
magma = cm.get_cmap("magma_r", 256)

# Convert the colormap to a list of hexadecimal colors
magma_hex = [rgb2hex(rgb) for rgb in magma(np.arange(256))]


# locations = {'sone': '2023-05-01', 'chambal': '2022-02-01'}
ids = list(locations.keys())
# dates = list(locations.values()['date'])

# colorbar_path  = Path(solara.website.__file__) / "colorbar_r.png"


class Map(geemap.Map):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_basemap("Esri.WorldImagery")
        # self.add_prediction(river=river_name.value, date=locations[river_name.value])
        self.add_prediction(ids[0], center=True)
        # self.add_ee_data()
        # self.add_layer_manager()
        self.add_inspector()
        self.name = "map"

        date_selector_dropdown = widgets.Dropdown(
            options=ids,
            description="River-Date",
        )
        date_selector_dropdown.value = ids[0]

        def on_value_change(change):
            # The new value is stored in the 'new' key of the change dictionary
            new_value = change["new"]

            print(f"The new value is {new_value}")
            self.add_prediction(new_value)

        # Attach the callback function to the dropdown
        date_selector_dropdown.observe(on_value_change, names="value")

        widget = widgets.VBox([date_selector_dropdown])
        self.add_widget(widget, position="bottomright")

    def parse_id(self, id):
        river = id.split("_")[0]
        date = id.split("_")[1]
        s2_path = locations[id]["uri_to_s2"]
        prediction_path = locations[id]["uri_to_prediction"]

        return s2_path, prediction_path, river, date

    def add_prediction(self, id, center=False):
        s2_path, prediction_path, river, date = self.parse_id(id)

        # display(river, date, "\n")

        # Load the prediction image
        prediction = ee.Image.loadGeoTIFF(prediction_path)

        mask = prediction.lte(1.0).And(prediction.gt(threshold))

        # Update the image to include the mask
        prediction = prediction.updateMask(mask)

        # Define visualization parameters with the viridis palette
        prediction_vis_params = {
            "min": 0,
            "max": 1,
            "palette": magma_hex,
            "opacity": 0.5,
        }

        # Load the S2 image
        s2_image = ee.Image.loadGeoTIFF(s2_path)
        mask_s2 = s2_image.neq(0)
        s2_image = s2_image.updateMask(mask_s2)
        # stretch s2 to 98% of the histogram

        # Add the S2 image
        s2_image_params = {
            "min": 0,
            "max": 3000,
            "bands": ["B3", "B2", "B1"],
            "gamma": 1.4,
        }

        # Map.addLayer(s1_image, s1_image_params, 'S1')
        self.addLayer(s2_image, s2_image_params, f"{river} RGB")
        # Add the prediction layer to the map
        self.addLayer(prediction, prediction_vis_params, f"{river} prediction")
        # self.add_colorbar(prediction_vis_params, orientation='vertical', position='bottomright')

        # center the map on the image
        if center:
            self.centerObject(prediction, int(zoom.value))


@solara.component
def Page():
    # with solara.Column(style={"min-width": "500px"}):
    with solara.Column():
        with solara.Card("This is a reactively-sized map."):
            Map.element(  # type: ignore
                zoom=zoom.value,
                on_zoom=zoom.set,
                # center=center.value,
                # on_center=center.set,
                scroll_wheel_zoom=True,
                add_google_map=True,
                height="500px",
            )
            solara.Text(f"Zoom: {zoom.value}")
            solara.Text(f"Center: {center.value}")
            solara.Image(colorbar_path)
