from clld.web.datatables.base import DataTable, LinkCol


class Phonemes(DataTable):
    def col_defs(self):
        return [LinkCol(self, "name")]


def includeme(config):
    config.register_datatable("phonemes", Phonemes)
