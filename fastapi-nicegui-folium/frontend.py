from fastapi import FastAPI

from nicegui import app, ui
import folium
import branca.colormap as cm
from localtileserver import TileClient, get_folium_tile_layer
import httpx
import matplotlib

async def call_download_cloud_object(item_uri:str):
    async with httpx.AsyncClient() as client:
        # Example GET request
        response = await client.get(f'http://127.0.0.1:8000/download-cloud-object/{item_uri}')
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to download blob from Google Cloud."}

async def call_convert_tif_to_mercator(tif_filename:str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f'http://127.0.0.1:8000/convert-tif-to-mercator/{tif_filename}')
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to convert and save .tif file."}

async def call_get_bounds_from_raster(tif_filename:str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f'http://127.0.0.1:8000/get-bounds-from-raster/{tif_filename}')
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Unable to get corner bounds from raster file."}

def init(fastapi_app: FastAPI) -> None:
    @ui.page("/")
    def show():
        with ui.header(elevated=True).style("background-color: #3874c8").classes(
            "items-center justify-between"
        ):
            ui.markdown("## **Sandmining Watch Visualizer**")
            ui.button(on_click=lambda: right_drawer.toggle(), text="Toggle Map Options", icon="menu").props(
                "flat color=white"
            )
        with ui.right_drawer(fixed=False).style("background-color: #ebf1fa").props(
            "bordered"
        ) as right_drawer:
            ui.markdown("## Options Menu")
            example_rivers = [
                "chambal",
                "ganga",
                "sone"
            ]
            example_dates = [
                "2022-02-01",
                "2022-05-01",
                "2022-10-01",
                "2022-03-01",
                "2023-10-01",
                "2023-11-01",
            ]
            ui.separator()
            ui.select(label="Select River of Interest", options=example_rivers, with_input=True, 
                      on_change=lambda e: ui.notify(e.value)).classes('w-40')
            ui.select(label="Select Date of Interest", options=example_dates, with_input=True, 
                      on_change=lambda e: ui.notify(e.value)).classes('w-40')
            switch = ui.switch('Toggle River Boundaries')
            #ui.label('Switch!').bind_visibility_from(switch, 'value')


        with ui.footer().style("background-color: #3874c8"):
            ui.label("FOOTER")
            # NOTE dark mode will be persistent for each user across tabs and server restarts
            ui.dark_mode().bind_value(app.storage.user, "dark_mode")
            ui.checkbox("dark mode").bind_value(app.storage.user, "dark_mode")

        ui.markdown("### Test Leaflet Basic Map")
        m = ui.leaflet(center=(51.505, -0.09))
        ui.label().bind_text_from(
            m, "center", lambda center: f"Center: {center[0]:.3f}, {center[1]:.3f}"
        )
        ui.label().bind_text_from(m, "zoom", lambda zoom: f"Zoom: {zoom}")

        with ui.grid(columns=2):
            ui.button("London", on_click=lambda: m.set_center((51.505, -0.090)))
            ui.button("Berlin", on_click=lambda: m.set_center((52.520, 13.405)))
            ui.button(icon="zoom_in", on_click=lambda: m.set_zoom(m.zoom + 1))
            ui.button(icon="zoom_out", on_click=lambda: m.set_zoom(m.zoom - 1))
        ui.separator()
        ui.markdown("### Test Folium iFrame embedding")
        map_width = 700
        map_height = 400
        bounds=[[24.87767926527418, 75.52379138719529], [26.877772963912907, 79.27387985276931]]
        x_center = (bounds[0][0] + bounds[1][0])/2
        y_center = (bounds[0][1] + bounds[1][1])/2
        client = TileClient("RGB.byte.wgs84_compressed.tif")
        t = get_folium_tile_layer(client, opacity=0.4, colormap="viridis", interactive=True, name="Chambal Compressed")
        m1 = folium.Map(
            location=client.center(),
            tiles="Esri.WorldImagery",
            zoom_start=client.default_zoom, 
            width=map_width, 
            height=map_height, 
            scrollWheelZoom=True
        )
        m1.get_root().width = f"{map_width}px"
        m1.get_root().height = f"{map_height}px"
        colormap = cm.linear.viridis
        folium.TileLayer('openstreetmap').add_to(m1)
        m1.add_child(t)
        colormap = cm.linear.viridis
        colormap.caption = "Probability of sandmining"
        m1.add_child(colormap)
        folium.LayerControl().add_to(m1)

        ui.label().bind_text_from(
            m1, "center", lambda center: f"Center: {center[0]:.3f}, {center[1]:.3f}"
        )
        ui.label().bind_text_from(m1, "zoom", lambda zoom: f"Zoom: {zoom}")
        iframe = m1.get_root()._repr_html_()
        ui.html(iframe).classes("w-full h-full")


    ui.run_with(
        fastapi_app,
        mount_path='/home',  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
        storage_secret='pick your private secret here',  # NOTE setting a secret is optional but allows for persistent storage per user
    )
