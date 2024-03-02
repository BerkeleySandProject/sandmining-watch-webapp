import solara


@solara.component
def Page():
    with solara.Column(align="center"):
        markdown = """
        ## Solara for Geospatial Applications
        
        ### Introduction

        A webapp demo to view predictions from the [Sand Mining Watch](https://github.com/BerkeleySandProject/sandmining-watch) project.

        Just a proof-of-concept for now. Not all features are working yet. More features will be added in the future.

        - Web App: <https://sandmining-watch.hf.space>
        - GitHub: <https://github.com/BerkeleySandProject/sandmining-watch>
        - Hugging Face: <https://huggingface.co/spaces/andoshah/sandmining-watch>


        ### Pages

        The prediction page currently contains predictions for different timestamps for the Chambal river in India.

        """

        solara.Markdown(markdown)
