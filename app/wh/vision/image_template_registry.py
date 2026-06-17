from app.wh.vision.image_template_loader import (
    ImageTemplateLoader
)


class ImageTemplateRegistry:

    def __init__(

        self,

        loader=None

    ):

        self.loader = (

            loader

            or

            ImageTemplateLoader()

        )

        self.templates = {

            "frame": [

                "frame_1.png",

                "frame_2.png",

                "frame_dark.png"

            ],

            "sash": [

                "sash_1.png",

                "sash_2.png"

            ]

        }

    def get(

        self,

        name

    ):

        return self.loader.load(

            name

        )

    def get_all(

        self,

        name

    ):

        template_names = (

            self.templates.get(

                name,

                [

                    name

                ]

            )

        )

        return [

            self.loader.load(

                template_name

            )

            for template_name

            in template_names

        ]