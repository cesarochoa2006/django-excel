from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import HttpResponse
import pyexcel as pe
import pyexcel_webio as webio


class ExcelMixin(webio.ExcelInput):
    def _get_file_extension(self):
        extension = self.name.split(".")[1]
        return extension
        
    def load_single_sheet(self, sheet_name=None, **keywords):
        return pe.load_from_memory(self._get_file_extension(), self.file.read(), sheet_name, **keywords)

    def load_book(self):
        return pe.load_book_from_memory(self._get_file_extension(), self.file.read())

    def save_to_database(self, model=None,
                         sheet_name=None, name_columns_by_row=0, name_rows_by_column=-1, **keywords):
        sheet = self.load_single_sheet(sheet_name=sheet_name,
                                       name_columns_by_row=name_columns_by_row,
                                       name_rows_by_column=name_rows_by_column,
                                       **keywords)
        if sheet:
            sheet.save_to_django_model(model)

    def save_book_to_database(self, models=None, **keywords):
        book = self.load_book(**keywords)
        if book:
            book.save_to_django_models(models)


class ExcelInMemoryUploadedFile(ExcelMixin, InMemoryUploadedFile):
    pass


class TemporaryUploadedExcelFile(ExcelMixin, TemporaryUploadedFile):
    pass


class ExcelMemoryFileUploadHandler(MemoryFileUploadHandler):
    def file_complete(self, file_size):
        if not self.activated:
            return
        self.file.seek(0)
        return ExcelInMemoryUploadedFile(
            file=self.file,
            field_name=self.field_name,
            name=self.file_name,
            content_type=self.content_type,
            size=file_size,
            charset=self.charset,
            content_type_extra=self.content_type_extra
        )

class TemporaryExcelFileUploadHandler(TemporaryFileUploadHandler):
    def new_file(self, file_name, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        super(TemporaryFileUploadHandler, self).new_file(file_name, *args, **kwargs)
        self.file = TemporaryUploadedExcelFile(self.file_name, self.content_type, 0, self.charset, self.content_type_extra)


webio.ExcelResponse = HttpResponse


from pyexcel_webio import (
    make_response,
    make_response_from_array,
    make_response_from_dict,
    make_response_from_records,
    make_response_from_book_dict,
)

def make_response_from_a_model(model, file_type, status=200, **keywords):
    sheet = pe.get_sheet(model, **keywords)
    return make_response(sheet, file_type, status, **keywords)

def make_response_from_models(models, file_type, status=200, **keywords):
    book = pe.get_book(models, **keywords)
    return make_response(book, file_type, status, **keywords)
