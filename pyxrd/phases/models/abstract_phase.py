# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from random import choice
import zipfile

from mvc.models.prop_intel import PropIntel

from pyxrd.generic.io import storables, Storable, COMPRESSION
from pyxrd.generic.models import DataModel

from pyxrd.calculations.data_objects import PhaseData
from pyxrd.calculations.phases import get_diffracted_intensity


@storables.register()
class AbstractPhase(DataModel, Storable):

    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="name", data_type=unicode, label="Name", is_column=True, has_widget=True, storable=True),
            PropIntel(name="G", data_type=int, label="# of components", is_column=True, has_widget=True, widget_type="entry", storable=True),
            PropIntel(name="R", data_type=int, label="Reichweite", is_column=True, has_widget=True, widget_type="entry"),
        ]
        store_id = "AbstractPhase"

    _data_object = None
    @property
    def data_object(self):
        return self._data_object

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    name = "New Phase"

    _display_color = "#FFB600"
    def get_display_color(self): return self._display_color
    def set_display_color(self, value):
        if self._display_color != value:
            with self.visuals_changed.hold_and_emit():
                self._display_color = value

    def get_G(self):
        return 0

    def get_R(self):
        return 0

    line_colors = [
        "#004488",
        "#FF4400",
        "#559911",
        "#770022",
        "#AACC00",
        "#441177",
    ]

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        my_kwargs = self.pop_kwargs(kwargs,
            "data_name", "data_G", "data_R",
            *[names[0] for names in AbstractPhase.Meta.get_local_storable_properties()]
        )
        super(AbstractPhase, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():

            self._data_object = PhaseData()

            self.name = self.get_kwarg(kwargs, self.name, "name", "data_name")
            self.display_color = self.get_kwarg(kwargs, choice(self.line_colors), "display_color")


    def __repr__(self):
        return "AbstractPhase(name='%s')" % (self.name)

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_json_references(self):
        pass # nothing to do, sub-classes should override

    def _pre_multi_save(self, phases):
        pass # nothing to do, sub-classes should override

    def _post_multi_save(self, phases):
        pass # nothing to do, sub-classes should override

    @classmethod
    def save_phases(cls, phases, filename):
        """
            Saves multiple phases to a single file.
        """
        ordered_phases = list(phases) # make a copy
        for phase in phases:
            phase._pre_multi_save()

        with zipfile.ZipFile(filename, 'w', compression=COMPRESSION) as zfile:
            for i, phase in enumerate(ordered_phases):
                zfile.writestr("%d###%s" % (i, phase.uuid), phase.dump_object())

        for phase in ordered_phases:
            phase._post_multi_save()

        # After export we change all the UUID's
        # This way, we're sure that we're not going to import objects with
        # duplicate UUID's!
        type(cls).object_pool.change_all_uuids()

    @classmethod
    def load_phases(cls, filename, parent=None):
        """
            Returns multiple phases loaded from a single file.
        """
        # Before import, we change all the UUID's
        # This way we're sure that we're not going to import objects
        # with duplicate UUID's!
        type(cls).object_pool.change_all_uuids()
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as zfile:
                for name in zfile.namelist():
                    # i, hs, uuid = name.partition("###")
                    # if uuid=='': uuid = i
                    yield cls.load_object(zfile.open(name), parent=parent)
        else:
            yield cls.load_object(filename, parent=parent)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_diffracted_intensity(self, range_theta, range_stl, *args):
        return get_diffracted_intensity(range_theta, range_stl, self.data_object)

    pass # end of class