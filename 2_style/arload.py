import os, re, sys, shutil, getpass, datetime, subprocess

from tank import Tank
import libLog, libData, libFunc
from Qt import QtWidgets, QtGui, QtCore, QtCompat

from arUtil import ArUtil
import arNotice

TITLE = "load"
LOG = libLog.init(script=TITLE)

class ArLoad(ArUtil):
    def __init__(self):
        super(ArLoad, self).__init__()
        
        module_path = os.path.dirname(__file__)
        path_ui = "/".join([module_path, "ui", TITLE + ".ui"])
        self.wgLoad = QtCompat.loadUi(path_ui)
        self.load_dir = ''
        self.load_file = ''

        software_extensions_items = self.data['software']['EXTENSION'].items()
        self.software_format = {y:x.upper() for x,y in software_extensions_items}
        self.software_keys = list(self.software_format.keys())

        # Clear lists and meta
        self.wgLoad.lstScene.clear()
        self.wgLoad.lstStatus.clear()
        self.wgLoad.lstSet.clear()
        self.clear_meta()

        self.resize_widget(self.wgLoad)
        self.wgLoad.show()
        LOG.info('START : ArLoad')

    def press_btn_accept(self):
        if not os.path.exists(self.load_file):
            status_text = f"Path doesn't exists: {self.load_file}"
            self.set_status(status_text, msg_type=3)
            return False
        
    def press_menu_item_add_folder(self):
        import arSaveAs
        self.save_as = arSaveAs.start(new_file=False)

    def _update_list(self, list_widget: QtWidgets.QListWidget, new_items: list[str]):
        list_widget.clear()
        if new_items:
            list_widget.addItems(sorted(new_items))
            list_widget.setCurrentRow(0)

    def press_menu_sort(self, list_widget, reverse=False):
        file_list = []
        widget_count = list_widget.count()
        
        for index in range(widget_count):
             item_text = list_widget.item(index).text()
             file_list.append(item_text)

        list_widget.clear()
        list_widget.addItems(sorted(file_list, reverse=reverse))

    def change_list_scene(self):
        current_item_txt = self.wgLoad.lstScene.currentItem().text()
        self.load_dir = self.data['project']['PATH'][current_item_txt]

        scene_steps_list = self.data['rules']['SCENES'][current_item_txt].split('/')
        self.scene_steps = len(scene_steps_list)
        
        if self.scene_steps < 5:
            self.wgLoad.lstAsset.hide()
        else:
            self.wgLoad.lstAsset.itemSelectionChanged.connect(self.change_lst_asset)
            self.wgLoad.lstAsset.show()

        file_list = libFunc.get_file_list(self.load_dir)
        self._update_list(self.wgLoad.lstSet, file_list)

    def change_lst_set(self):
        new_path = f"{self.load_dir}/{self.wgLoad.lstSet.currentItem().text()}"
        file_list = libFunc.get_file_list(new_path)
        
        widget = self.wgLoad.lstTask if self.scene_steps < 5 else self.wgLoad.lstAsset
        self._update_list(widget, sorted(file_list))

    def change_lst_asset(self):
        current_set_item_txt    = self.wgLoad.lstSet.currentItem().text()
        current_asset_item_txt  = self.wgLoad.lstAsset.currentItem().text()

        new_path = f"{self.load_dir}/{current_set_item_txt}/{current_asset_item_txt}"

        file_list = libFunc.get_file_list(new_path)
        self._update_list(self.wgLoad.lstTask, sorted(file_list))

    def fill_meta(self):
        self.wgPreview.lblTitle.setText(self.file_name)

        file_time = os.path.getmtime(self.load_file)
        file_timestamp = datetime.datetime.fromtimestamp(file_time)
        date_text = str(file_timestamp).split(".")[0]

        self.wgPreview.lblDate.setText(date_text)   # Apply date_text to widget.

        file_size = os.path.getsize(self.load_file) / (1024*1024.0) # Convert to MB
        size_label_txt = "{0:.2f}".format(file_size) + " MB"
        self.wgPreview.lblSize.setText(size_label_txt)  # Apply size_label_txt to widget.

    def clear_meta(self):
        self.wgPreview.lblUser.setText('')
        self.wgPreview.lblTitle.setText('')
        self.wgPreview.lblDate.setText('')


def execute_the_class_ar_load():
    global main_widget
    main_widget = ArLoad()
