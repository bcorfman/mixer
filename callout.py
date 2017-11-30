from tvtk.api import tvtk


class Callout:
    """ A Pythonic wrapper for a TVTK text actor that makes it easier to create a callout above an object
    on the 3D scene. """
    def __init__(self, text="", **args):
        self.__text_actor = tvtk.TextActor()
        if args.get('justification'):
            self.__text_actor.text_property.justification = args['justification']
        if args.get('font_size'):
            self.__text_actor.text_property.font_size = args['font_size']
        if args.get('color'):
            self.__text_actor.text_property.color = args['color']
        self.__text_actor.position_coordinate.coordinate_system = 'world'
        if args.get('position'):
            self.__text_actor.position_coordinate.value = args['position']
        self.__text_actor.input = text

    @property
    def position(self):
        return self.__text_actor.position_coordinate.value

    @position.setter
    def position(self, value):
        self.__text_actor.position_coordinate.value = value

    @property
    def text(self):
        return self.__text_actor.input

    @text.setter
    def text(self, value):
        self.__text_actor.input = value

    @property
    def actor(self):
        return self.__text_actor

    @property
    def visible(self):
        return self.__text_actor.visibility

    @visible.setter
    def visible(self, val):
        self.__text_actor.visibility = val
