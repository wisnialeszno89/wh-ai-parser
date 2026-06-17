def find_ui_object(

    ui_graph,

    object_id
):

    for obj in ui_graph.objects:

        if obj.id == object_id:

            return obj

    return None