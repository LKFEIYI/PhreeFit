# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui6.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################'
import multiprocessing
import numpy as np
import main_cal as mc
import pandas as pd
import time
import os
import pyqtgraph as pg
from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect, Qt, QThread, QAbstractTableModel, Signal)
from PySide6.QtGui import (QAction, QFont, QIntValidator, QDoubleValidator)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGroupBox, QLabel, QLineEdit, QMainWindow,
                               QMenu, QMenuBar, QPushButton, QRadioButton, QStackedWidget, QStatusBar, QTableView,
                               QTextEdit, QVBoxLayout, QWidget, QMessageBox, QFileDialog, QInputDialog)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(810, 608)
        self.actionDatabase_path = QAction(MainWindow)
        self.actionDatabase_path.setObjectName(u"actionDatabase_path")
        self.actionparameters = QAction(MainWindow)
        self.actionparameters.setObjectName(u"actionparameters")
        self.actionpp = QAction(MainWindow)
        self.actionpp.setObjectName(u"actionpp")
        self.actionTitration = QAction(MainWindow)
        self.actionTitration.setObjectName(u"actionTitration")
        font = QFont()
        font.setFamilies([u"Arial"])
        self.actionTitration.setFont(font)
        self.actionPlot = QAction(MainWindow)
        self.actionPlot.setObjectName(u"actionPlot")
        self.actionPlot.setFont(font)
        self.actionAdvanced = QAction(MainWindow)
        self.actionAdvanced.setObjectName(u"actionAdvanced")
        self.actionAdvanced.setFont(font)
        self.actiondifferential_evolution = QAction(MainWindow)
        self.actiondifferential_evolution.setObjectName(u"actiondifferential_evolution")
        self.actiondifferential_evolution.setCheckable(True)
        self.actiondifferential_evolution.setChecked(True)
        self.actiondifferential_evolution.setFont(font)
        self.actionDual_annealing = QAction(MainWindow)
        self.actionDual_annealing.setObjectName(u"actionDual_annealing")
        self.actionDual_annealing.setCheckable(True)
        self.actionDual_annealing.setFont(font)
        self.actionnelder_mead = QAction(MainWindow)
        self.actionnelder_mead.setObjectName(u"actionnelder_mead")
        self.actionnelder_mead.setCheckable(True)
        self.actionnelder_mead.setFont(font)
        self.actionDatabase_folder = QAction(MainWindow)
        self.actionDatabase_folder.setObjectName(u"actionDatabase_folder")
        self.actionDatabase_folder.setFont(font)
        self.actionOutput_folder = QAction(MainWindow)
        self.actionOutput_folder.setObjectName(u"actionOutput_folder")
        self.actionOutput_folder.setFont(font)
        self.actionDisabled = QAction(MainWindow)
        self.actionDisabled.setObjectName(u"actionDisabled")
        self.actionDisabled.setCheckable(True)
        self.actionDisabled.setChecked(True)
        self.actionDisabled.setFont(font)
        self.actionEnabled = QAction(MainWindow)
        self.actionEnabled.setObjectName(u"actionEnabled")
        self.actionEnabled.setCheckable(True)
        self.actionEnabled.setChecked(False)
        self.actionEnabled.setFont(font)
        self.actionData_folder = QAction(MainWindow)
        self.actionData_folder.setObjectName(u"actionData_folder")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(0, 10, 801, 571))
        self.stackedWidget.setFont(font)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.label_28 = QLabel(self.page)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setGeometry(QRect(230, 330, 71, 21))
        self.label_27 = QLabel(self.page)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setGeometry(QRect(230, 300, 71, 21))
        self.groupBox_2 = QGroupBox(self.page)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(220, 150, 231, 131))
        self.label_12 = QLabel(self.groupBox_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(180, 60, 54, 12))
        self.radioButton_fx = QRadioButton(self.groupBox_2)
        self.radioButton_fx.setObjectName(u"radioButton_fx")
        self.radioButton_fx.setGeometry(QRect(100, 20, 89, 16))
        self.radioButton_ds = QRadioButton(self.groupBox_2)
        self.radioButton_ds.setObjectName(u"radioButton_ds")
        self.radioButton_ds.setGeometry(QRect(100, 40, 89, 16))
        self.lineEdit_base = QLineEdit(self.groupBox_2)
        self.lineEdit_base.setObjectName(u"lineEdit_base")
        self.lineEdit_base.setGeometry(QRect(90, 60, 81, 20))
        self.comboBox_bs = QComboBox(self.groupBox_2)
        self.comboBox_bs.addItem("")
        self.comboBox_bs.addItem("")
        self.comboBox_bs.setObjectName(u"comboBox_bs")
        self.comboBox_bs.setGeometry(QRect(10, 60, 69, 22))
        self.label_mix = QLabel(self.groupBox_2)
        self.label_mix.setObjectName(u"label_mix")
        self.label_mix.setGeometry(QRect(10, 20, 81, 21))
        self.comboBox_ad = QComboBox(self.groupBox_2)
        self.comboBox_ad.addItem("")
        self.comboBox_ad.addItem("")
        self.comboBox_ad.setObjectName(u"comboBox_ad")
        self.comboBox_ad.setGeometry(QRect(10, 90, 69, 22))
        self.lineEdit_acid = QLineEdit(self.groupBox_2)
        self.lineEdit_acid.setObjectName(u"lineEdit_acid")
        self.lineEdit_acid.setGeometry(QRect(90, 90, 81, 20))
        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setGeometry(QRect(180, 90, 54, 12))
        self.groupBox_3 = QGroupBox(self.page)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(220, 20, 231, 121))
        self.lineEdit_vol = QLineEdit(self.groupBox_3)
        self.lineEdit_vol.setObjectName(u"lineEdit_vol")
        self.lineEdit_vol.setGeometry(QRect(122, 80, 101, 20))
        self.label_cs = QLabel(self.groupBox_3)
        self.label_cs.setObjectName(u"label_cs")
        self.label_cs.setGeometry(QRect(20, 20, 71, 21))
        self.label_ph = QLabel(self.groupBox_3)
        self.label_ph.setObjectName(u"label_ph")
        self.label_ph.setGeometry(QRect(20, 50, 71, 21))
        self.label_vol = QLabel(self.groupBox_3)
        self.label_vol.setObjectName(u"label_vol")
        self.label_vol.setGeometry(QRect(10, 80, 101, 21))
        self.lineEdit_ph = QLineEdit(self.groupBox_3)
        self.lineEdit_ph.setObjectName(u"lineEdit_ph")
        self.lineEdit_ph.setGeometry(QRect(100, 50, 113, 20))
        self.lineEdit_cs = QLineEdit(self.groupBox_3)
        self.lineEdit_cs.setObjectName(u"lineEdit_cs")
        self.lineEdit_cs.setGeometry(QRect(100, 20, 113, 20))
        self.lineEdit_iter = QLineEdit(self.page)
        self.lineEdit_iter.setObjectName(u"lineEdit_iter")
        self.lineEdit_iter.setGeometry(QRect(290, 300, 61, 20))
        self.pushButton_db = QPushButton(self.page)
        self.pushButton_db.setObjectName(u"pushButton_db")
        self.pushButton_db.setGeometry(QRect(30, 10, 171, 51))
        self.groupBox_4 = QGroupBox(self.page)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(230, 450, 551, 101))
        self.textEdit_res = QTextEdit(self.groupBox_4)
        self.textEdit_res.setObjectName(u"textEdit_res")
        self.textEdit_res.setGeometry(QRect(0, 30, 551, 71))
        self.pushButton_rd = QPushButton(self.page)
        self.pushButton_rd.setObjectName(u"pushButton_rd")
        self.pushButton_rd.setGeometry(QRect(30, 60, 171, 51))
        self.lineEdit_temp = QLineEdit(self.page)
        self.lineEdit_temp.setObjectName(u"lineEdit_temp")
        self.lineEdit_temp.setGeometry(QRect(290, 330, 61, 20))
        self.pushButton_opt = QPushButton(self.page)
        self.pushButton_opt.setObjectName(u"pushButton_opt")
        self.pushButton_opt.setGeometry(QRect(370, 290, 81, 101))
        self.tableView = QTableView(self.page)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setGeometry(QRect(10, 120, 201, 391))
        self.groupBox = QGroupBox(self.page)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(460, 20, 331, 421))
        self.textEdit_sf = QTextEdit(self.groupBox)
        self.textEdit_sf.setObjectName(u"textEdit_sf")
        self.textEdit_sf.setGeometry(QRect(0, 320, 331, 101))
        self.pushButton_addsf = QPushButton(self.groupBox)
        self.pushButton_addsf.setObjectName(u"pushButton_addsf")
        self.pushButton_addsf.setGeometry(QRect(10, 290, 111, 23))
        self.comboBox_mdl = QComboBox(self.groupBox)
        self.comboBox_mdl.addItem("")
        self.comboBox_mdl.addItem("")
        self.comboBox_mdl.addItem("")
        self.comboBox_mdl.setObjectName(u"comboBox_mdl")
        self.comboBox_mdl.setGeometry(QRect(110, 120, 69, 22))
        self.lineEdit_sarea = QLineEdit(self.groupBox)
        self.lineEdit_sarea.setObjectName(u"lineEdit_sarea")
        self.lineEdit_sarea.setGeometry(QRect(110, 60, 113, 20))
        self.lineEdit_sname = QLineEdit(self.groupBox)
        self.lineEdit_sname.setObjectName(u"lineEdit_sname")
        self.lineEdit_sname.setGeometry(QRect(110, 30, 113, 20))
        self.label_25 = QLabel(self.groupBox)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setGeometry(QRect(20, 30, 81, 21))
        self.lineEdit_smass = QLineEdit(self.groupBox)
        self.lineEdit_smass.setObjectName(u"lineEdit_smass")
        self.lineEdit_smass.setGeometry(QRect(110, 90, 113, 20))
        self.label_26 = QLabel(self.groupBox)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setGeometry(QRect(20, 60, 81, 21))
        self.label_29 = QLabel(self.groupBox)
        self.label_29.setObjectName(u"label_29")
        self.label_29.setGeometry(QRect(230, 60, 81, 21))
        self.label_30 = QLabel(self.groupBox)
        self.label_30.setObjectName(u"label_30")
        self.label_30.setGeometry(QRect(20, 90, 81, 21))
        self.label_31 = QLabel(self.groupBox)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setGeometry(QRect(230, 90, 81, 21))
        self.label_32 = QLabel(self.groupBox)
        self.label_32.setObjectName(u"label_32")
        self.label_32.setGeometry(QRect(20, 120, 81, 21))
        self.pushButton_review = QPushButton(self.groupBox)
        self.pushButton_review.setObjectName(u"pushButton_review")
        self.pushButton_review.setGeometry(QRect(120, 290, 131, 23))
        self.label_33 = QLabel(self.groupBox)
        self.label_33.setObjectName(u"label_33")
        self.label_33.setGeometry(QRect(110, 150, 81, 21))
        self.label_34 = QLabel(self.groupBox)
        self.label_34.setObjectName(u"label_34")
        self.label_34.setGeometry(QRect(220, 150, 81, 21))
        self.checkBox_dpro = QCheckBox(self.groupBox)
        self.checkBox_dpro.setObjectName(u"checkBox_dpro")
        self.checkBox_dpro.setGeometry(QRect(20, 170, 91, 16))
        self.checkBox_pro = QCheckBox(self.groupBox)
        self.checkBox_pro.setObjectName(u"checkBox_pro")
        self.checkBox_pro.setGeometry(QRect(20, 200, 91, 16))
        self.lineEdit_ikdp = QLineEdit(self.groupBox)
        self.lineEdit_ikdp.setObjectName(u"lineEdit_ikdp")
        self.lineEdit_ikdp.setGeometry(QRect(120, 170, 51, 20))
        self.lineEdit_dplb = QLineEdit(self.groupBox)
        self.lineEdit_dplb.setObjectName(u"lineEdit_dplb")
        self.lineEdit_dplb.setGeometry(QRect(200, 170, 51, 20))
        self.lineEdit_dpub = QLineEdit(self.groupBox)
        self.lineEdit_dpub.setObjectName(u"lineEdit_dpub")
        self.lineEdit_dpub.setGeometry(QRect(260, 170, 51, 20))
        self.lineEdit_ikp = QLineEdit(self.groupBox)
        self.lineEdit_ikp.setObjectName(u"lineEdit_ikp")
        self.lineEdit_ikp.setGeometry(QRect(120, 200, 51, 20))
        self.lineEdit_plb = QLineEdit(self.groupBox)
        self.lineEdit_plb.setObjectName(u"lineEdit_plb")
        self.lineEdit_plb.setGeometry(QRect(200, 200, 51, 20))
        self.lineEdit_pub = QLineEdit(self.groupBox)
        self.lineEdit_pub.setObjectName(u"lineEdit_pub")
        self.lineEdit_pub.setGeometry(QRect(260, 200, 51, 20))
        self.label_35 = QLabel(self.groupBox)
        self.label_35.setObjectName(u"label_35")
        self.label_35.setGeometry(QRect(20, 230, 81, 21))
        self.lineEdit_isite = QLineEdit(self.groupBox)
        self.lineEdit_isite.setObjectName(u"lineEdit_isite")
        self.lineEdit_isite.setGeometry(QRect(90, 230, 51, 20))
        self.label_36 = QLabel(self.groupBox)
        self.label_36.setObjectName(u"label_36")
        self.label_36.setGeometry(QRect(160, 230, 41, 21))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(8)
        self.label_36.setFont(font1)
        self.lineEdit_siteub = QLineEdit(self.groupBox)
        self.lineEdit_siteub.setObjectName(u"lineEdit_siteub")
        self.lineEdit_siteub.setGeometry(QRect(260, 230, 51, 20))
        self.lineEdit_sitelb = QLineEdit(self.groupBox)
        self.lineEdit_sitelb.setObjectName(u"lineEdit_sitelb")
        self.lineEdit_sitelb.setGeometry(QRect(200, 230, 51, 20))
        self.pushButton_cls = QPushButton(self.groupBox)
        self.pushButton_cls.setObjectName(u"pushButton_cls")
        self.pushButton_cls.setGeometry(QRect(250, 290, 61, 23))
        self.label_37 = QLabel(self.groupBox)
        self.label_37.setObjectName(u"label_37")
        self.label_37.setGeometry(QRect(10, 260, 111, 21))
        self.lineEdit_icap = QLineEdit(self.groupBox)
        self.lineEdit_icap.setObjectName(u"lineEdit_icap")
        self.lineEdit_icap.setGeometry(QRect(120, 260, 31, 20))
        self.lineEdit_caplb = QLineEdit(self.groupBox)
        self.lineEdit_caplb.setObjectName(u"lineEdit_caplb")
        self.lineEdit_caplb.setGeometry(QRect(200, 260, 51, 20))
        self.label_38 = QLabel(self.groupBox)
        self.label_38.setObjectName(u"label_38")
        self.label_38.setGeometry(QRect(160, 260, 41, 21))
        self.label_38.setFont(font1)
        self.lineEdit_capub = QLineEdit(self.groupBox)
        self.lineEdit_capub.setObjectName(u"lineEdit_capub")
        self.lineEdit_capub.setGeometry(QRect(260, 260, 51, 20))
        self.lineEdit_cycle = QLineEdit(self.page)
        self.lineEdit_cycle.setObjectName(u"lineEdit_cycle")
        self.lineEdit_cycle.setGeometry(QRect(290, 360, 61, 20))
        self.label_39 = QLabel(self.page)
        self.label_39.setObjectName(u"label_39")
        self.label_39.setGeometry(QRect(230, 360, 51, 21))
        self.pushButton_stp = QPushButton(self.page)
        self.pushButton_stp.setObjectName(u"pushButton_stp")
        self.pushButton_stp.setGeometry(QRect(370, 400, 81, 41))
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.verticalLayoutWidget = QWidget(self.page_2)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 791, 541))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget.addWidget(self.page_2)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.pushButton_db_2 = QPushButton(self.page_3)
        self.pushButton_db_2.setObjectName(u"pushButton_db_2")
        self.pushButton_db_2.setGeometry(QRect(10, 0, 161, 51))
        self.pushButton_rd_2 = QPushButton(self.page_3)
        self.pushButton_rd_2.setObjectName(u"pushButton_rd_2")
        self.pushButton_rd_2.setGeometry(QRect(10, 50, 161, 51))
        self.tableView_2 = QTableView(self.page_3)
        self.tableView_2.setObjectName(u"tableView_2")
        self.tableView_2.setGeometry(QRect(10, 130, 161, 391))
        self.checkBox = QCheckBox(self.page_3)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setGeometry(QRect(20, 110, 101, 16))
        self.groupBox_5 = QGroupBox(self.page_3)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.groupBox_5.setGeometry(QRect(180, 0, 241, 141))
        self.lineEdit_reactant = QLineEdit(self.groupBox_5)
        self.lineEdit_reactant.setObjectName(u"lineEdit_reactant")
        self.lineEdit_reactant.setGeometry(QRect(70, 110, 61, 20))
        self.label_cs_2 = QLabel(self.groupBox_5)
        self.label_cs_2.setObjectName(u"label_cs_2")
        self.label_cs_2.setGeometry(QRect(10, 50, 71, 21))
        self.label_ph_2 = QLabel(self.groupBox_5)
        self.label_ph_2.setObjectName(u"label_ph_2")
        self.label_ph_2.setGeometry(QRect(10, 80, 71, 21))
        self.label_vol_2 = QLabel(self.groupBox_5)
        self.label_vol_2.setObjectName(u"label_vol_2")
        self.label_vol_2.setGeometry(QRect(10, 110, 61, 21))
        self.lineEdit_cs_2 = QLineEdit(self.groupBox_5)
        self.lineEdit_cs_2.setObjectName(u"lineEdit_cs_2")
        self.lineEdit_cs_2.setGeometry(QRect(90, 80, 111, 20))
        self.lineEdit_cation = QLineEdit(self.groupBox_5)
        self.lineEdit_cation.setObjectName(u"lineEdit_cation")
        self.lineEdit_cation.setGeometry(QRect(50, 50, 51, 20))
        self.label_cs_3 = QLabel(self.groupBox_5)
        self.label_cs_3.setObjectName(u"label_cs_3")
        self.label_cs_3.setGeometry(QRect(110, 50, 71, 21))
        self.lineEdit_anion = QLineEdit(self.groupBox_5)
        self.lineEdit_anion.setObjectName(u"lineEdit_anion")
        self.lineEdit_anion.setGeometry(QRect(160, 50, 61, 20))
        self.lineEdit_moles = QLineEdit(self.groupBox_5)
        self.lineEdit_moles.setObjectName(u"lineEdit_moles")
        self.lineEdit_moles.setGeometry(QRect(140, 110, 61, 20))
        self.label_vol_3 = QLabel(self.groupBox_5)
        self.label_vol_3.setObjectName(u"label_vol_3")
        self.label_vol_3.setGeometry(QRect(200, 110, 61, 21))
        self.label_cs_4 = QLabel(self.groupBox_5)
        self.label_cs_4.setObjectName(u"label_cs_4")
        self.label_cs_4.setGeometry(QRect(10, 20, 51, 21))
        self.lineEdit_ph_4 = QLineEdit(self.groupBox_5)
        self.lineEdit_ph_4.setObjectName(u"lineEdit_ph_4")
        self.lineEdit_ph_4.setGeometry(QRect(60, 20, 71, 20))
        self.label_initial_vol = QLabel(self.groupBox_5)
        self.label_initial_vol.setObjectName(u"label_initial_vol")
        self.label_initial_vol.setGeometry(QRect(140, 20, 41, 21))
        self.lineEdit_ph_5 = QLineEdit(self.groupBox_5)
        self.lineEdit_ph_5.setObjectName(u"lineEdit_ph_5")
        self.lineEdit_ph_5.setGeometry(QRect(180, 20, 51, 20))
        self.groupBox_6 = QGroupBox(self.page_3)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setGeometry(QRect(180, 150, 241, 161))
        self.label_13 = QLabel(self.groupBox_6)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setGeometry(QRect(180, 60, 54, 12))
        self.radioButton_fx_2 = QRadioButton(self.groupBox_6)
        self.radioButton_fx_2.setObjectName(u"radioButton_fx_2")
        self.radioButton_fx_2.setGeometry(QRect(90, 20, 89, 16))
        self.radioButton_ds_2 = QRadioButton(self.groupBox_6)
        self.radioButton_ds_2.setObjectName(u"radioButton_ds_2")
        self.radioButton_ds_2.setGeometry(QRect(150, 20, 89, 16))
        self.lineEdit_base_2 = QLineEdit(self.groupBox_6)
        self.lineEdit_base_2.setObjectName(u"lineEdit_base_2")
        self.lineEdit_base_2.setGeometry(QRect(90, 60, 81, 20))
        self.comboBox_bs_2 = QComboBox(self.groupBox_6)
        self.comboBox_bs_2.addItem("")
        self.comboBox_bs_2.addItem("")
        self.comboBox_bs_2.setObjectName(u"comboBox_bs_2")
        self.comboBox_bs_2.setGeometry(QRect(10, 60, 69, 22))
        self.label_mix_2 = QLabel(self.groupBox_6)
        self.label_mix_2.setObjectName(u"label_mix_2")
        self.label_mix_2.setGeometry(QRect(10, 20, 81, 21))
        self.comboBox_ad_2 = QComboBox(self.groupBox_6)
        self.comboBox_ad_2.addItem("")
        self.comboBox_ad_2.addItem("")
        self.comboBox_ad_2.addItem("")
        self.comboBox_ad_2.setObjectName(u"comboBox_ad_2")
        self.comboBox_ad_2.setGeometry(QRect(10, 90, 69, 22))
        self.lineEdit_acid_2 = QLineEdit(self.groupBox_6)
        self.lineEdit_acid_2.setObjectName(u"lineEdit_acid_2")
        self.lineEdit_acid_2.setGeometry(QRect(90, 90, 81, 20))
        self.label_16 = QLabel(self.groupBox_6)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setGeometry(QRect(180, 100, 54, 12))
        self.checkBox_7 = QCheckBox(self.groupBox_6)
        self.checkBox_7.setObjectName(u"checkBox_7")
        self.checkBox_7.setGeometry(QRect(10, 40, 161, 16))
        self.label_mix_5 = QLabel(self.groupBox_6)
        self.label_mix_5.setObjectName(u"label_mix_5")
        self.label_mix_5.setGeometry(QRect(10, 120, 81, 21))
        self.textEdit = QTextEdit(self.groupBox_6)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(90, 120, 104, 31))
        self.groupBox_7 = QGroupBox(self.page_3)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.groupBox_7.setGeometry(QRect(180, 320, 241, 51))
        self.comboBox = QComboBox(self.groupBox_7)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(10, 20, 69, 22))
        self.lineEdit_output = QLineEdit(self.groupBox_7)
        self.lineEdit_output.setObjectName(u"lineEdit_output")
        self.lineEdit_output.setGeometry(QRect(100, 20, 113, 20))
        self.lineEdit_cycle_2 = QLineEdit(self.page_3)
        self.lineEdit_cycle_2.setObjectName(u"lineEdit_cycle_2")
        self.lineEdit_cycle_2.setGeometry(QRect(250, 440, 61, 20))
        self.label_40 = QLabel(self.page_3)
        self.label_40.setObjectName(u"label_40")
        self.label_40.setGeometry(QRect(190, 440, 51, 21))
        self.pushButton_opt_2 = QPushButton(self.page_3)
        self.pushButton_opt_2.setObjectName(u"pushButton_opt_2")
        self.pushButton_opt_2.setGeometry(QRect(330, 370, 81, 61))
        self.label_41 = QLabel(self.page_3)
        self.label_41.setObjectName(u"label_41")
        self.label_41.setGeometry(QRect(190, 410, 71, 21))
        self.pushButton_stp_2 = QPushButton(self.page_3)
        self.pushButton_stp_2.setObjectName(u"pushButton_stp_2")
        self.pushButton_stp_2.setGeometry(QRect(330, 430, 81, 41))
        self.label_42 = QLabel(self.page_3)
        self.label_42.setObjectName(u"label_42")
        self.label_42.setGeometry(QRect(190, 380, 71, 21))
        self.lineEdit_iter_2 = QLineEdit(self.page_3)
        self.lineEdit_iter_2.setObjectName(u"lineEdit_iter_2")
        self.lineEdit_iter_2.setGeometry(QRect(250, 380, 61, 20))
        self.lineEdit_temp_2 = QLineEdit(self.page_3)
        self.lineEdit_temp_2.setObjectName(u"lineEdit_temp_2")
        self.lineEdit_temp_2.setGeometry(QRect(250, 410, 61, 20))
        self.groupBox_8 = QGroupBox(self.page_3)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.groupBox_8.setGeometry(QRect(180, 470, 611, 81))
        self.textEdit_res_2 = QTextEdit(self.groupBox_8)
        self.textEdit_res_2.setObjectName(u"textEdit_res_2")
        self.textEdit_res_2.setGeometry(QRect(0, 20, 611, 61))
        self.groupBox_9 = QGroupBox(self.page_3)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.groupBox_9.setGeometry(QRect(430, 0, 361, 471))
        self.textEdit_sf_2 = QTextEdit(self.groupBox_9)
        self.textEdit_sf_2.setObjectName(u"textEdit_sf_2")
        self.textEdit_sf_2.setGeometry(QRect(10, 390, 341, 81))
        self.pushButton_addsf_2 = QPushButton(self.groupBox_9)
        self.pushButton_addsf_2.setObjectName(u"pushButton_addsf_2")
        self.pushButton_addsf_2.setGeometry(QRect(230, 80, 91, 23))
        self.comboBox_mdl_2 = QComboBox(self.groupBox_9)
        self.comboBox_mdl_2.addItem("")
        self.comboBox_mdl_2.addItem("")
        self.comboBox_mdl_2.addItem("")
        self.comboBox_mdl_2.addItem("")
        self.comboBox_mdl_2.setObjectName(u"comboBox_mdl_2")
        self.comboBox_mdl_2.setGeometry(QRect(130, 110, 69, 22))
        self.lineEdit_sarea_2 = QLineEdit(self.groupBox_9)
        self.lineEdit_sarea_2.setObjectName(u"lineEdit_sarea_2")
        self.lineEdit_sarea_2.setGeometry(QRect(110, 50, 61, 20))
        self.lineEdit_sname_2 = QLineEdit(self.groupBox_9)
        self.lineEdit_sname_2.setObjectName(u"lineEdit_sname_2")
        self.lineEdit_sname_2.setGeometry(QRect(110, 20, 61, 20))
        self.label_43 = QLabel(self.groupBox_9)
        self.label_43.setObjectName(u"label_43")
        self.label_43.setGeometry(QRect(20, 20, 81, 21))
        self.lineEdit_smass_2 = QLineEdit(self.groupBox_9)
        self.lineEdit_smass_2.setObjectName(u"lineEdit_smass_2")
        self.lineEdit_smass_2.setGeometry(QRect(110, 80, 61, 20))
        self.label_44 = QLabel(self.groupBox_9)
        self.label_44.setObjectName(u"label_44")
        self.label_44.setGeometry(QRect(20, 50, 81, 21))
        self.label_45 = QLabel(self.groupBox_9)
        self.label_45.setObjectName(u"label_45")
        self.label_45.setGeometry(QRect(180, 50, 41, 21))
        self.label_46 = QLabel(self.groupBox_9)
        self.label_46.setObjectName(u"label_46")
        self.label_46.setGeometry(QRect(20, 80, 81, 21))
        self.label_47 = QLabel(self.groupBox_9)
        self.label_47.setObjectName(u"label_47")
        self.label_47.setGeometry(QRect(180, 80, 21, 21))
        self.label_48 = QLabel(self.groupBox_9)
        self.label_48.setObjectName(u"label_48")
        self.label_48.setGeometry(QRect(20, 110, 101, 21))
        self.pushButton_addreact = QPushButton(self.groupBox_9)
        self.pushButton_addreact.setObjectName(u"pushButton_addreact")
        self.pushButton_addreact.setGeometry(QRect(10, 360, 101, 23))
        self.label_49 = QLabel(self.groupBox_9)
        self.label_49.setObjectName(u"label_49")
        self.label_49.setGeometry(QRect(100, 160, 81, 21))
        self.label_50 = QLabel(self.groupBox_9)
        self.label_50.setObjectName(u"label_50")
        self.label_50.setGeometry(QRect(230, 160, 81, 21))
        self.label_51 = QLabel(self.groupBox_9)
        self.label_51.setObjectName(u"label_51")
        self.label_51.setGeometry(QRect(20, 140, 61, 21))
        self.lineEdit_reaction = QLineEdit(self.groupBox_9)
        self.lineEdit_reaction.setObjectName(u"lineEdit_reaction")
        self.lineEdit_reaction.setGeometry(QRect(70, 140, 281, 20))
        self.lineEdit_siteub_2 = QLineEdit(self.groupBox_9)
        self.lineEdit_siteub_2.setObjectName(u"lineEdit_siteub_2")
        self.lineEdit_siteub_2.setGeometry(QRect(260, 180, 51, 20))
        self.lineEdit_isite_2 = QLineEdit(self.groupBox_9)
        self.lineEdit_isite_2.setObjectName(u"lineEdit_isite_2")
        self.lineEdit_isite_2.setGeometry(QRect(110, 180, 51, 20))
        self.lineEdit_sitelb_2 = QLineEdit(self.groupBox_9)
        self.lineEdit_sitelb_2.setObjectName(u"lineEdit_sitelb_2")
        self.lineEdit_sitelb_2.setGeometry(QRect(190, 180, 51, 20))
        self.checkBox_site = QCheckBox(self.groupBox_9)
        self.checkBox_site.setObjectName(u"checkBox_site")
        self.checkBox_site.setGeometry(QRect(10, 180, 91, 21))
        self.checkBox_c1 = QCheckBox(self.groupBox_9)
        self.checkBox_c1.setObjectName(u"checkBox_c1")
        self.checkBox_c1.setGeometry(QRect(10, 210, 91, 21))
        self.checkBox_c2 = QCheckBox(self.groupBox_9)
        self.checkBox_c2.setObjectName(u"checkBox_c2")
        self.checkBox_c2.setGeometry(QRect(10, 240, 91, 21))
        self.checkBox_logk = QCheckBox(self.groupBox_9)
        self.checkBox_logk.setObjectName(u"checkBox_logk")
        self.checkBox_logk.setGeometry(QRect(10, 270, 91, 21))
        self.lineEdit_ic1 = QLineEdit(self.groupBox_9)
        self.lineEdit_ic1.setObjectName(u"lineEdit_ic1")
        self.lineEdit_ic1.setGeometry(QRect(110, 210, 51, 20))
        self.lineEdit_ic2 = QLineEdit(self.groupBox_9)
        self.lineEdit_ic2.setObjectName(u"lineEdit_ic2")
        self.lineEdit_ic2.setGeometry(QRect(110, 240, 51, 20))
        self.lineEdit_ik = QLineEdit(self.groupBox_9)
        self.lineEdit_ik.setObjectName(u"lineEdit_ik")
        self.lineEdit_ik.setGeometry(QRect(110, 270, 51, 20))
        self.lineEdit_ic1ub = QLineEdit(self.groupBox_9)
        self.lineEdit_ic1ub.setObjectName(u"lineEdit_ic1ub")
        self.lineEdit_ic1ub.setGeometry(QRect(260, 210, 51, 20))
        self.lineEdit_ic1lb = QLineEdit(self.groupBox_9)
        self.lineEdit_ic1lb.setObjectName(u"lineEdit_ic1lb")
        self.lineEdit_ic1lb.setGeometry(QRect(190, 210, 51, 20))
        self.lineEdit_ic2lb = QLineEdit(self.groupBox_9)
        self.lineEdit_ic2lb.setObjectName(u"lineEdit_ic2lb")
        self.lineEdit_ic2lb.setGeometry(QRect(190, 240, 51, 20))
        self.lineEdit_ic2ub = QLineEdit(self.groupBox_9)
        self.lineEdit_ic2ub.setObjectName(u"lineEdit_ic2ub")
        self.lineEdit_ic2ub.setGeometry(QRect(260, 240, 51, 20))
        self.lineEdit_iklb = QLineEdit(self.groupBox_9)
        self.lineEdit_iklb.setObjectName(u"lineEdit_iklb")
        self.lineEdit_iklb.setGeometry(QRect(190, 270, 51, 20))
        self.lineEdit_ikub = QLineEdit(self.groupBox_9)
        self.lineEdit_ikub.setObjectName(u"lineEdit_ikub")
        self.lineEdit_ikub.setGeometry(QRect(260, 270, 51, 20))
        self.comboBox_charge = QComboBox(self.groupBox_9)
        self.comboBox_charge.addItem("")
        self.comboBox_charge.addItem("")
        self.comboBox_charge.setObjectName(u"comboBox_charge")
        self.comboBox_charge.setGeometry(QRect(110, 330, 69, 22))
        self.checkBox_z1 = QCheckBox(self.groupBox_9)
        self.checkBox_z1.setObjectName(u"checkBox_z1")
        self.checkBox_z1.setGeometry(QRect(10, 300, 61, 21))
        self.label_52 = QLabel(self.groupBox_9)
        self.label_52.setObjectName(u"label_52")
        self.label_52.setGeometry(QRect(10, 160, 51, 21))
        self.lineEdit_iz1 = QLineEdit(self.groupBox_9)
        self.lineEdit_iz1.setObjectName(u"lineEdit_iz1")
        self.lineEdit_iz1.setGeometry(QRect(110, 300, 51, 20))
        self.lineEdit_iz1lb = QLineEdit(self.groupBox_9)
        self.lineEdit_iz1lb.setObjectName(u"lineEdit_iz1lb")
        self.lineEdit_iz1lb.setGeometry(QRect(190, 300, 51, 20))
        self.lineEdit_iz1ub = QLineEdit(self.groupBox_9)
        self.lineEdit_iz1ub.setObjectName(u"lineEdit_iz1ub")
        self.lineEdit_iz1ub.setGeometry(QRect(260, 300, 51, 20))
        self.lineEdit_totalz = QLineEdit(self.groupBox_9)
        self.lineEdit_totalz.setObjectName(u"lineEdit_totalz")
        self.lineEdit_totalz.setGeometry(QRect(190, 330, 51, 20))
        self.pushButton_delreact = QPushButton(self.groupBox_9)
        self.pushButton_delreact.setObjectName(u"pushButton_delreact")
        self.pushButton_delreact.setGeometry(QRect(120, 360, 91, 23))
        self.pushButton_delsf = QPushButton(self.groupBox_9)
        self.pushButton_delsf.setObjectName(u"pushButton_delsf")
        self.pushButton_delsf.setGeometry(QRect(230, 110, 91, 23))
        self.pushButton_cls_4 = QPushButton(self.groupBox_9)
        self.pushButton_cls_4.setObjectName(u"pushButton_cls_4")
        self.pushButton_cls_4.setGeometry(QRect(220, 360, 91, 23))
        self.lineEdit_sformula = QLineEdit(self.groupBox_9)
        self.lineEdit_sformula.setObjectName(u"lineEdit_sformula")
        self.lineEdit_sformula.setGeometry(QRect(240, 20, 113, 20))
        self.label_53 = QLabel(self.groupBox_9)
        self.label_53.setObjectName(u"label_53")
        self.label_53.setGeometry(QRect(180, 20, 81, 21))
        self.stackedWidget.addWidget(self.page_3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 810, 23))
        self.menuTitration = QMenu(self.menubar)
        self.menuTitration.setObjectName(u"menuTitration")
        self.menuAlgorithm = QMenu(self.menubar)
        self.menuAlgorithm.setObjectName(u"menuAlgorithm")
        self.menuDirectory = QMenu(self.menubar)
        self.menuDirectory.setObjectName(u"menuDirectory")
        self.menuInit_protonation = QMenu(self.menubar)
        self.menuInit_protonation.setObjectName(u"menuInit_protonation")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuTitration.menuAction())
        self.menubar.addAction(self.menuAlgorithm.menuAction())
        self.menubar.addAction(self.menuDirectory.menuAction())
        self.menubar.addAction(self.menuInit_protonation.menuAction())
        self.menuTitration.addAction(self.actionTitration)
        self.menuTitration.addAction(self.actionPlot)
        self.menuTitration.addAction(self.actionAdvanced)
        self.menuAlgorithm.addAction(self.actiondifferential_evolution)
        self.menuAlgorithm.addAction(self.actionDual_annealing)
        self.menuAlgorithm.addAction(self.actionnelder_mead)
        self.menuDirectory.addAction(self.actionDatabase_folder)
        self.menuDirectory.addAction(self.actionData_folder)
        self.menuDirectory.addAction(self.actionOutput_folder)
        self.menuInit_protonation.addAction(self.actionDisabled)
        self.menuInit_protonation.addAction(self.actionEnabled)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(MainWindow)
        # setupUi
        self.pushButton_db.clicked.connect(self.load_database)
        self.pushButton_rd.clicked.connect(self.showOpendialog)
        self.pushButton_opt.clicked.connect(self.optimize_data)
        self.pushButton_addsf.clicked.connect(self.check_sp)
        self.pushButton_review.clicked.connect(self.show_surface)
        self.pushButton_cls.clicked.connect(self.clear_sp)
        self.actionTitration.triggered.connect(self.titration_view)
        self.actionPlot.triggered.connect(self.plot_view)

        self.pushButton_stp.clicked.connect(self.stop_thread)
        # the advanced window
        self.actionAdvanced.triggered.connect(self.advanced_view)
        self.pushButton_db_2.clicked.connect(self.load_database)
        self.pushButton_rd_2.clicked.connect(self.showOpendialog2)
        self.pushButton_addsf_2.clicked.connect(self.update_surface)
        self.pushButton_delsf.clicked.connect(self.del_surf)
        self.pushButton_addreact.clicked.connect(self.add_reaction)
        self.pushButton_delreact.clicked.connect(self.del_reaction)
        self.pushButton_cls_4.clicked.connect(self.clear_all)
        self.pushButton_opt_2.clicked.connect(self.advanced_opt)
        self.pushButton_stp_2.clicked.connect(self.stop_thread2)

        self.actiondifferential_evolution.triggered.connect(self.differential_evolution)
        self.actionDual_annealing.triggered.connect(self.dual_annealing)
        self.actionnelder_mead.triggered.connect(self.nelder_mead)

        self.checkBox.stateChanged.connect(self.label_change_2)
        self.radioButton_fx_2.toggled.connect(self.label_change_2)
        self.radioButton_ds_2.toggled.connect(self.label_change_2)
        self.radioButton_ds.toggled.connect(self.label_change_1)
        self.radioButton_fx_2.toggled.connect(self.label_change_1)

        self.actionDatabase_folder.triggered.connect(self.set_database_folder)
        self.actionOutput_folder.triggered.connect(self.set_output_folder)
        self.actionData_folder.triggered.connect(self.set_data_folder)
        self.actionEnabled.triggered.connect(self.enable_surf_eq)
        self.actionDisabled.triggered.connect(self.disable_surf_eq)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"PhreeFit", None))
        self.actionDatabase_path.setText(QCoreApplication.translate("MainWindow", u"Database path", None))
        self.actionparameters.setText(QCoreApplication.translate("MainWindow", u"Parameters", None))
        self.actionpp.setText(QCoreApplication.translate("MainWindow", u"pp", None))
        self.actionTitration.setText(QCoreApplication.translate("MainWindow", u"Titration", None))
        self.actionPlot.setText(QCoreApplication.translate("MainWindow", u"Plot", None))
        self.actionAdvanced.setText(QCoreApplication.translate("MainWindow", u"Advanced", None))
        self.actiondifferential_evolution.setText(
            QCoreApplication.translate("MainWindow", u"Differential evolution", None))
        self.actionDual_annealing.setText(QCoreApplication.translate("MainWindow", u"Dual annealing", None))
        self.actionnelder_mead.setText(QCoreApplication.translate("MainWindow", u"Nelder Mead", None))
        self.actionDatabase_folder.setText(QCoreApplication.translate("MainWindow", u"Database path", None))
        self.actionOutput_folder.setText(QCoreApplication.translate("MainWindow", u"Output path", None))
        self.actionDisabled.setText(QCoreApplication.translate("MainWindow", u"Disabled", None))
        # self.actionpH_2.setText(QCoreApplication.translate("MainWindow", u"pH", None))
        # self.actionIS_2.setText(QCoreApplication.translate("MainWindow", u"IS", None))
        self.actionEnabled.setText(QCoreApplication.translate("MainWindow", u"Enabled", None))
        self.actionData_folder.setText(QCoreApplication.translate("MainWindow", u"Data path", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", u"T", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Max iter:", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Titration solution", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"mol/L", None))
        self.radioButton_fx.setText(QCoreApplication.translate("MainWindow", u"Fix pH", None))
        self.radioButton_ds.setText(QCoreApplication.translate("MainWindow", u"Dissolution", None))
        self.comboBox_bs.setItemText(0, QCoreApplication.translate("MainWindow", u"NaOH", None))
        self.comboBox_bs.setItemText(1, QCoreApplication.translate("MainWindow", u"KOH", None))

        self.label_mix.setText(QCoreApplication.translate("MainWindow", u"Solution type", None))
        self.comboBox_ad.setItemText(0, QCoreApplication.translate("MainWindow", u"HCl", None))
        self.comboBox_ad.setItemText(1, QCoreApplication.translate("MainWindow", u"HNO3", None))

        self.label_15.setText(QCoreApplication.translate("MainWindow", u"mol/L", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Initial Solution", None))
        self.label_cs.setText(QCoreApplication.translate("MainWindow", u"IS mol/L", None))
        self.label_ph.setText(QCoreApplication.translate("MainWindow", u"Initial pH", None))
        self.label_vol.setText(QCoreApplication.translate("MainWindow", u"Initial volume mL", None))
        self.pushButton_db.setText(QCoreApplication.translate("MainWindow", u"Database", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Results", None))
        self.pushButton_rd.setText(QCoreApplication.translate("MainWindow", u"Read Titration data", None))
        self.pushButton_opt.setText(QCoreApplication.translate("MainWindow", u"Optimize", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Set Surface parameters", None))
        self.pushButton_addsf.setText(QCoreApplication.translate("MainWindow", u"Add surface", None))
        self.comboBox_mdl.setItemText(0, QCoreApplication.translate("MainWindow", u"NEM", None))
        self.comboBox_mdl.setItemText(1, QCoreApplication.translate("MainWindow", u"CCM", None))
        self.comboBox_mdl.setItemText(2, QCoreApplication.translate("MainWindow", u"GDDL", None))

        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Surface name", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"Surface area", None))
        self.label_29.setText(QCoreApplication.translate("MainWindow", u"m2/g", None))
        self.label_30.setText(QCoreApplication.translate("MainWindow", u"Surface mass", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", u"g", None))
        self.label_32.setText(QCoreApplication.translate("MainWindow", u"Surface model", None))
        self.pushButton_review.setText(QCoreApplication.translate("MainWindow", u"Review reactions", None))
        self.label_33.setText(QCoreApplication.translate("MainWindow", u"Initial Logk", None))
        self.label_34.setText(QCoreApplication.translate("MainWindow", u"LogK bounds", None))
        self.checkBox_dpro.setText(QCoreApplication.translate("MainWindow", u"Acidic site", None))
        self.checkBox_pro.setText(QCoreApplication.translate("MainWindow", u"Basic site", None))
        self.label_35.setText(QCoreApplication.translate("MainWindow", u"Site (mole)", None))
        self.label_36.setText(QCoreApplication.translate("MainWindow", u"Bounds", None))
        self.pushButton_cls.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", u"Capacitance (F/m2)", None))
        self.label_38.setText(QCoreApplication.translate("MainWindow", u"Bounds", None))
        self.label_39.setText(QCoreApplication.translate("MainWindow", u"Cores", None))
        self.pushButton_stp.setText(QCoreApplication.translate("MainWindow", u"Terminate", None))
        self.pushButton_db_2.setText(QCoreApplication.translate("MainWindow", u"Database", None))
        self.pushButton_rd_2.setText(QCoreApplication.translate("MainWindow", u"Read exp data", None))
        self.checkBox.setText(QCoreApplication.translate("MainWindow", u"Titration", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Initial Solution", None))
        self.label_cs_2.setText(QCoreApplication.translate("MainWindow", u"Cation", None))
        self.label_ph_2.setText(QCoreApplication.translate("MainWindow", u"Conc (mol/L)", None))
        self.label_vol_2.setText(QCoreApplication.translate("MainWindow", u"Reactant", None))
        self.label_cs_3.setText(QCoreApplication.translate("MainWindow", u"Anion", None))
        self.label_vol_3.setText(QCoreApplication.translate("MainWindow", u"mol/L", None))
        self.label_cs_4.setText(QCoreApplication.translate("MainWindow", u"Initial pH", None))
        self.label_initial_vol.setText(QCoreApplication.translate("MainWindow", u"V (mL)", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Equilibrium or Titration solution", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"mol/L", None))
        self.radioButton_fx_2.setText(QCoreApplication.translate("MainWindow", u"Fix pH", None))
        self.radioButton_ds_2.setText(QCoreApplication.translate("MainWindow", u"Dissolve", None))
        self.comboBox_bs_2.setItemText(0, QCoreApplication.translate("MainWindow", u"NaOH", None))
        self.comboBox_bs_2.setItemText(1, QCoreApplication.translate("MainWindow", u"KOH", None))

        self.label_mix_2.setText(QCoreApplication.translate("MainWindow", u"Type", None))
        self.comboBox_ad_2.setItemText(0, QCoreApplication.translate("MainWindow", u"HCl", None))
        self.comboBox_ad_2.setItemText(1, QCoreApplication.translate("MainWindow", u"H2SO4", None))
        self.comboBox_ad_2.setItemText(2, QCoreApplication.translate("MainWindow", u"HNO3", None))

        self.label_16.setText(QCoreApplication.translate("MainWindow", u"mol/L", None))
        self.checkBox_7.setText(QCoreApplication.translate("MainWindow", u"Automatic pH", None))
        self.label_mix_5.setText(QCoreApplication.translate("MainWindow", u"Eq Phase:", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("MainWindow", u"Output", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"totals", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"activities", None))
        self.comboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"molalities ", None))

        self.label_40.setText(QCoreApplication.translate("MainWindow", u"Cores", None))
        self.pushButton_opt_2.setText(QCoreApplication.translate("MainWindow", u"Optimize", None))
        self.label_41.setText(QCoreApplication.translate("MainWindow", u"T", None))
        self.pushButton_stp_2.setText(QCoreApplication.translate("MainWindow", u"Terminate", None))
        self.label_42.setText(QCoreApplication.translate("MainWindow", u"Max iter:", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", u"Results", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("MainWindow", u"Set Surface parameters", None))
        self.pushButton_addsf_2.setText(QCoreApplication.translate("MainWindow", u"Add surface", None))
        self.comboBox_mdl_2.setItemText(0, QCoreApplication.translate("MainWindow", u"NEM", None))
        self.comboBox_mdl_2.setItemText(1, QCoreApplication.translate("MainWindow", u"CCM", None))
        self.comboBox_mdl_2.setItemText(2, QCoreApplication.translate("MainWindow", u"GDDL", None))
        self.comboBox_mdl_2.setItemText(3, QCoreApplication.translate("MainWindow", u"CDMUSIC", None))

        self.label_43.setText(QCoreApplication.translate("MainWindow", u"Surface name", None))
        self.label_44.setText(QCoreApplication.translate("MainWindow", u"Surface area", None))
        self.label_45.setText(QCoreApplication.translate("MainWindow", u"m2/g", None))
        self.label_46.setText(QCoreApplication.translate("MainWindow", u"Surface mass", None))
        self.label_47.setText(QCoreApplication.translate("MainWindow", u"g", None))
        self.label_48.setText(QCoreApplication.translate("MainWindow", u"Model selection", None))
        self.pushButton_addreact.setText(QCoreApplication.translate("MainWindow", u"Add reaction", None))
        self.label_49.setText(QCoreApplication.translate("MainWindow", u"Initial value", None))
        self.label_50.setText(QCoreApplication.translate("MainWindow", u"Bounds", None))
        self.label_51.setText(QCoreApplication.translate("MainWindow", u"Reaction", None))
        self.lineEdit_reaction.setText("")
        self.checkBox_site.setText(QCoreApplication.translate("MainWindow", u"Site (moles)", None))
        self.checkBox_c1.setText(QCoreApplication.translate("MainWindow", u"C1 (F/m2)", None))
        self.checkBox_c2.setText(QCoreApplication.translate("MainWindow", u"C2 (F/m2)", None))
        self.checkBox_logk.setText(QCoreApplication.translate("MainWindow", u"   log_k", None))
        self.comboBox_charge.setItemText(0, QCoreApplication.translate("MainWindow", u"z0+z1", None))
        self.comboBox_charge.setItemText(1, QCoreApplication.translate("MainWindow", u"z1+zd", None))

        self.checkBox_z1.setText(QCoreApplication.translate("MainWindow", u"   z1", None))
        self.label_52.setText(QCoreApplication.translate("MainWindow", u"Fix", None))
        self.pushButton_delreact.setText(QCoreApplication.translate("MainWindow", u"Del reaction", None))
        self.pushButton_delsf.setText(QCoreApplication.translate("MainWindow", u"Del surface", None))
        self.pushButton_cls_4.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.label_53.setText(QCoreApplication.translate("MainWindow", u"Formula", None))
        self.menuTitration.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menuAlgorithm.setTitle(QCoreApplication.translate("MainWindow", u"Algorithm", None))
        self.menuDirectory.setTitle(QCoreApplication.translate("MainWindow", u"Directory", None))
        self.menuInit_protonation.setTitle(QCoreApplication.translate("MainWindow", u"Pre-equilibrate", None))
        # retranslateUi
        self.lineEdit_ikp.setText("0")
        self.lineEdit_ikdp.setText("0")
        self.lineEdit_dplb.setText("-10")
        self.lineEdit_dpub.setText("10")
        self.lineEdit_plb.setText("-10")
        self.lineEdit_pub.setText("10")
        self.lineEdit_isite.setText("0.0001")
        self.lineEdit_siteub.setText("0.01")
        self.lineEdit_sitelb.setText("0")
        self.lineEdit_iter.setText("1000")
        self.lineEdit_temp.setText("6000")
        self.radioButton_ds.setChecked(True)
        self.radioButton_ds_2.setChecked(True)
        self.lineEdit_icap.setText("1")
        self.lineEdit_caplb.setText("0")
        self.lineEdit_capub.setText("5")
        self.lineEdit_cycle.setText("1")
        self.pushButton_stp.setEnabled(False)
        self.lineEdit_base.setText("0")
        self.lineEdit_acid.setText("0")
        self.lineEdit_temp.setValidator(QIntValidator())
        self.lineEdit_iter.setValidator(QIntValidator())
        self.lineEdit_sarea.setValidator(QDoubleValidator())
        self.lineEdit_smass.setValidator(QDoubleValidator())
        self.lineEdit_cs.setValidator(QDoubleValidator())
        self.lineEdit_vol.setValidator(QDoubleValidator())
        self.lineEdit_ph.setValidator(QDoubleValidator())
        self.textEdit_sf.setReadOnly(True)
        self.textEdit_res.setReadOnly(True)
        self.lineEdit_ik.setText("0")
        self.lineEdit_iklb.setText("-10")
        self.lineEdit_ikub.setText("10")
        self.lineEdit_isite_2.setText("0.0001")
        self.lineEdit_sitelb_2.setText("0")
        self.lineEdit_siteub_2.setText("0.01")
        self.lineEdit_ic1.setText("1")
        self.lineEdit_ic1lb.setText("0")
        self.lineEdit_ic1ub.setText("5")
        self.lineEdit_ic2.setText("1")
        self.lineEdit_ic2lb.setText("0")
        self.lineEdit_ic2ub.setText("1")
        self.lineEdit_iter_2.setText("1000")
        self.lineEdit_temp_2.setText("6000")
        self.radioButton_ds.setChecked(True)
        self.lineEdit_iz1.setText("1")
        self.lineEdit_iz1lb.setText("-1")
        self.lineEdit_iz1ub.setText("1")
        self.lineEdit_totalz.setText("1")
        self.lineEdit_cycle_2.setText("1")
        self.pushButton_stp_2.setEnabled(False)
        self.lineEdit_base_2.setText("0")
        self.lineEdit_acid_2.setText("0")
        self.lineEdit_ph_5.setText("1000")
        self.checkBox_logk.setChecked(True)
        self.checkBox_site.setChecked(True)
        self.checkBox_c1.setChecked(True)
        self.checkBox_c2.setChecked(True)
        self.checkBox_z1.setChecked(True)
        self.lineEdit_temp_2.setValidator(QIntValidator())
        self.lineEdit_cycle.setValidator(QIntValidator())
        self.lineEdit_cycle_2.setValidator(QIntValidator())
        self.lineEdit_iter_2.setValidator(QIntValidator())
        self.lineEdit_sarea_2.setValidator(QDoubleValidator())
        self.lineEdit_smass_2.setValidator(QDoubleValidator())
        self.lineEdit_cs_2.setValidator(QDoubleValidator())
        self.lineEdit_ph_4.setValidator(QDoubleValidator())
        self.lineEdit_ph_5.setValidator(QDoubleValidator())

        self.method_selected = "Differential evolution"
        self.op_obj = []
        self.opad = []
        self.surf_eq = None
        #self.task_name=None
        pg.setConfigOptions(leftButtonPan=False)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.w_plt = pg.PlotWidget()
        self.verticalLayout.addWidget(self.w_plt)
        font_plot = QFont()
        font_plot.setPixelSize(16)
        font_plot.setFamily("Arial")

        self.w_plt.getAxis("left").setStyle(tickFont=font_plot, tickTextOffset=8)

        self.w_plt.getAxis("bottom").setStyle(tickFont=font_plot, tickTextOffset=8)

        self.label_change_1()
        self.label_change_2()

        #load config file
        self.config_file=ConfigFile()
        self.config_file.load_config_file()
        self.database_folder = self.config_file.database_directory
        self.output_folder = self.config_file.output_directory
        self.data_folder = self.config_file.data_directory

    def showOpendialog(self):
        try:
            filename = QFileDialog.getOpenFileName(None, "Open data", dir=self.data_folder)
            if filename[0] != "":
                data_review = pd.read_csv(filename[0])
                data_review=data_review.dropna(axis=1,how="all")
                data_review=data_review.dropna(axis=0)
                self.multi_is = False
                if len(data_review.columns) == 2:
                    data_review.columns = ["pH", "volume"]
                    self.mix_data = data_review["volume"].values
                elif len(data_review.columns) == 3:
                    data_review.columns = ["pH", "volume", "IS"]
                    self.mix_data = data_review.groupby("IS", sort=False)
                    self.multi_is = True
                self.ph_res = data_review["pH"].values
                model = PandasModel(data_review)
                self.tableView.setModel(model)
                # self.plot_res()
            else:
                QMessageBox.information(None, "warning", "Please choose a file",
                                        QMessageBox.Yes | QMessageBox.No)
        except Exception as error_msg:
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(None, "Error", "Please choose a correct csv file",
                                QMessageBox.Yes | QMessageBox.No)

    def showOpendialog2(self):
        try:
            filename = QFileDialog.getOpenFileName(None, "Open data", dir=self.data_folder)
            if filename[0] != "":
                data_review = pd.read_csv(filename[0])
                data_review=data_review.dropna(axis=1,how="all")
                data_review=data_review.dropna(axis=0)
                self.multi_is_ad = False
                if self.checkBox.isChecked() == False:
                    second_col = "amounts"
                    self.ph_res_ad = data_review.iloc[:, 1].values
                    self.mix_data_ad = data_review.iloc[:, 0].values
                else:
                    second_col = "volume"
                    self.ph_res_ad = data_review.iloc[:, 0].values
                    self.mix_data_ad = data_review.iloc[:, 1].values
                if len(data_review.columns) == 2:
                    data_review.columns = ["pH", second_col]
                elif len(data_review.columns) == 3:
                    data_review.columns = ["pH", second_col, "IS"]
                    self.mix_data_ad = data_review.groupby("IS", sort=False)
                    self.multi_is_ad = True
                else:
                    QMessageBox.information(None, "Warning", "Please choose a correct file with 2 or 3 columns",
                                            QMessageBox.Yes | QMessageBox.No)
                model = PandasModel(data_review)
                self.tableView_2.setModel(model)
                # self.plot_res()
            else:
                QMessageBox.information(None, "Warning", "Please choose a file",
                                        QMessageBox.Yes | QMessageBox.No)
        except Exception as error_msg:
            write_log(str(error_msg), self.output_folder)
            QMessageBox.warning(None, "Error", "Please choose a correct csv file",
                                QMessageBox.Yes | QMessageBox.No)

    def load_database(self):
        database_path = QFileDialog.getOpenFileName(None, "Open database", dir=self.database_folder)[0]
        if database_path != "":
            with open(database_path, "r", encoding="UTF-8") as file:
                self.database = file.read()

    def add_surface(self):
        tem_sp = mc.SurfaceSpecies2()
        temp_name = self.lineEdit_sname.text().strip().capitalize()
        tem_sp.add_surface(surfacename=temp_name, surface_ms=temp_name + "OH", mass=self.lineEdit_smass.text(),
                           sites=(float(self.lineEdit_sitelb.text()), float(self.lineEdit_siteub.text())),
                           area=self.lineEdit_sarea.text(), sites_initial=float(self.lineEdit_isite.text()),
                           c1_initial=float(self.lineEdit_icap.text()),
                           c1=(float(self.lineEdit_caplb.text()), float(self.lineEdit_capub.text())), c2=0)
        if self.checkBox_pro.isChecked() == True:
            if float(self.lineEdit_ikp.text())<float(self.lineEdit_plb.text()) or float(self.lineEdit_ikp.text())>float(self.lineEdit_pub.text()):
                QMessageBox.information(None, "warning", "The initial guess of log_k should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)

            tem_sp.add_reactions(reactions=tem_sp.surface_name + "OH" + " + H+ = " + tem_sp.surface_name + "OH2+",
                                     k_initial=float(self.lineEdit_ikp.text()),
                                     k=(float(self.lineEdit_plb.text()), float(self.lineEdit_pub.text())), z0d=True,
                                     ztotal=1, z1=1)

        if self.checkBox_dpro.isChecked() == True:
            if float(self.lineEdit_ikdp.text())<float(self.lineEdit_dplb.text()) or float(self.lineEdit_ikdp.text())>float(self.lineEdit_dpub.text()):
                QMessageBox.information(None, "warning", "The initial guess of log_k should be within the bounds",
                                        QMessageBox.Yes | QMessageBox.No)

            tem_sp.add_reactions(reactions=tem_sp.surface_name + "OH" + " = " + tem_sp.surface_name + "O-" + " + H+",
                                     k_initial=float(self.lineEdit_ikdp.text()),
                                     k=(float(self.lineEdit_dplb.text()), float(self.lineEdit_dpub.text())), z0d=True,
                                     ztotal=1, z1=1)
        return tem_sp

    def check_sp(self):
        sp_name = []
        for obj in self.op_obj:
            sp_name.append(obj.surface_name)
        if self.lineEdit_sname.text().strip().capitalize() != "":
            if sp_name.count(self.lineEdit_sname.text().strip().capitalize()) == 0:
                self.op_obj.append(self.add_surface())

            else:
                self.op_obj.pop(sp_name.index(self.lineEdit_sname.text().strip().capitalize()))
                self.op_obj.append(self.add_surface())

    def show_surface(self):
        surface_reaction = ""
        if self.actionEnabled.isChecked() == True:
            surface_reaction += "The surface will equilibrate with a solution before titration ( pH: " + str(
                self.surf_eq[0]) + ", " \
                                + "IS:" + str(self.surf_eq[1]) + ")\n"
        for obj in self.op_obj:
            surface_reaction += obj.surface_name + "\n"
            surface_reaction += str(obj.sfinitial[0]) + " bounds: " + str(obj.surface_sites[0]) + " - " + str(
                obj.surface_sites[1]) + "\n"
            for react in obj.surface_reactions.keys():
                surface_reaction += react + "\n"
                surface_reaction += "\t" + "initial_log_k: " + str(obj.surface_reactions[react][4]) + "\n"
                surface_reaction += "\t" + "log_k bounds: " + str(obj.surface_reactions[react][0][0]) + " - " + str(
                    obj.surface_reactions[react][0][1]) + "\n"
        self.textEdit_sf.setText(surface_reaction)

    def optimize_data(self):
        try:
            # print(self.output_folder)
            task_name = QInputDialog.getText(None, "Task name", "Input here")[0]
            self.config_file.update_config_file([self.data_folder,self.database_folder,self.output_folder])
            num_process = min([int(self.lineEdit_cycle.text(), multiprocessing.cpu_count())])
            pt = mc.Adsorption(self.comboBox_mdl.currentText())
            if self.multi_is == False:
                Na = [float(self.lineEdit_cs.text())]
            elif self.multi_is == True:
                Na = list(self.mix_data.groups.keys())
            initial_ph = float(self.lineEdit_ph.text())
            initial_volume = float(self.lineEdit_vol.text())
            pt.species_definition(self.database, None)
            pt.initial_solution(Na, initial_pH=initial_ph, cation="Na", anion="Cl", metal={})
            pt.set_type_acid(type_acid=self.comboBox_ad.currentText(), type_base=self.comboBox_bs.currentText())
            if self.radioButton_fx.isChecked() == True:
                type_solution = "fix_pH"
                pt.mix_solution(type_solution=type_solution, base_pH=float(self.lineEdit_base.text()),
                                acid_pH=float(self.lineEdit_acid.text()))
            elif self.radioButton_ds.isChecked() == True:
                type_solution = "dissolution"
                pt.mix_solution(type_solution=type_solution, base_mass=float(self.lineEdit_base.text()),
                                acid_mass=float(self.lineEdit_acid.text()))
            else:
                QMessageBox.information(None, "warning", "Please check your input in dissolution",
                                        QMessageBox.Yes | QMessageBox.No)
            if self.actionEnabled.isChecked() == True and self.surf_eq != None:
                pt.equilibrate_solution(self.surf_eq[1], self.surf_eq[0])
            for i in range(0, len(self.op_obj)):
                # print(self.op_obj[i].surface_name)
                if i == len(self.op_obj) - 1:
                    pt.add_surface(self.op_obj[i])
                else:
                    self.op_obj[i].reset_cap(1, 1)
                    pt.add_surface(self.op_obj[i])
            pt.selected_output({})
            pt.mix_action(initial_volume=initial_volume, mix_volume=self.mix_data)
            pt.get_bounds()
            self.work = WorkThreadAdvanced()
            self.pushButton_opt.setEnabled(False)
            self.comboBox_mdl.setEnabled(False)
            self.work.set_pa(pt, self.ph_res, int(self.lineEdit_iter.text()), int(self.lineEdit_temp.text()), mix=0,
                             method=self.method_selected, process_num=num_process,task=task_name)
            self.work.signals.connect(self.display_results)
            self.work.start()
            self.pushButton_stp.setEnabled(True)
        except Exception as e:
            write_log(str(e), self.output_folder)
            self.pushButton_opt.setEnabled(True)
            self.comboBox_mdl.setEnabled(True)

    def display_results(self, ssss):
        self.pushButton_opt.setEnabled(True)
        self.comboBox_mdl.setEnabled(True)
        self.pushButton_stp.setEnabled(False)
        if ssss["iterations"] < int(self.lineEdit_iter.text()) and self.method_selected == "Differential evolution":
            QMessageBox.information(None, "warning", "The iterations of DE method is rather few, please rerun or change some settings",
                                   QMessageBox.Yes | QMessageBox.No)
        if ssss["successful"] == True:
            log_temp = self.comboBox_mdl.currentText()
            self.textEdit_res.append(ssss["Task"]+'\n'+ssss["eva"] + "\n" + ssss["time"] + "\n")
            log_temp += ssss["surface"]
            write_log(ssss["Task"]+'\n'+ssss["eva"] + log_temp + "\n" + ssss["time"], self.output_folder)
            write_results(self.ph_res, ssss["model"],ssss["speciation"], self.output_folder)
            self.plot_res(ssss["model"], titration=True, view=False)
        else:
            self.textEdit_res.append(ssss["Task"]+'\n'+ssss["error"] + "\n")
            write_log(ssss["Task"]+'\n'+ssss["error"], self.output_folder)

    def clear_sp(self):
        self.op_obj.clear()

    def plot_view(self):
        self.stackedWidget.setCurrentIndex(1)

    def titration_view(self):
        self.stackedWidget.setCurrentIndex(0)

    def plot_res(self, model_res, titration=False, view=False):
        self.w_plt.addLegend()
        r_symbol = ('o', 's', 't', 't1', 't2', 't3', 'd', '+', 'x', 'p')
        r_color = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'd', 'l', 's')
        self.w_plt.clear()
        x_label = "volume"
        y_label = "pH"
        label_style = {"font": "Arial", "color": "#000", "font-size": "16pt"}
        if titration == False:
            self.w_plt.getAxis("left").setLabel(self.lineEdit_output.text() + " mol/L", **label_style)
            self.w_plt.getAxis("bottom").setLabel("pH", **label_style)
            x_label = "pH"
            y_label = "amounts"
        else:
            self.w_plt.getAxis("left").setLabel("pH", **label_style)
            self.w_plt.getAxis("bottom").setLabel("Volume (mL)", **label_style)
        if view == False:  # titration view
            multi_is = self.multi_is
            x_data = self.mix_data
            y_data = self.ph_res
        else:  # ad view
            multi_is = self.multi_is_ad
            x_data = self.mix_data_ad
            y_data = self.ph_res_ad
        if multi_is == False:
            self.w_plt.plot(x_data, y_data, pen=None, symbol=r_symbol[0], symbolBrush=r_color[0],
                            name="exp_data")
            self.w_plt.plot(x_data, model_res, pen=pg.mkPen(color="r", width=2), name="model")
        else:
            na = list(x_data.groups.keys())
            j = 0
            for i in range(0, len(na)):
                x1 = x_data.get_group(na[i])[x_label].to_list()
                self.w_plt.plot(x1, x_data.get_group(na[i])[y_label].to_list(),
                                pen=None, symbol=r_symbol[i], symbolBrush=r_color[i], name=str(na[i]))
                self.w_plt.plot(x1, model_res[j:j + len(x1)], pen=pg.mkPen(color=r_color[i], width=2), name=str(na[i]))
                j += len(x1)

    def stop_thread(self):
        self.work.terminate()
        write_log("Terminated by user", self.output_folder)
        self.pushButton_stp.setEnabled(False)
        self.pushButton_opt.setEnabled(True)
        self.comboBox_mdl.setEnabled(True)

    def advanced_view(self):
        self.stackedWidget.setCurrentIndex(2)

    def add_surface2(self):
        tem_sp = mc.SurfaceSpecies2()
        current_sname = self.lineEdit_sname_2.text().strip().capitalize()

        if self.checkBox_site.isChecked() == True:
            site = float(self.lineEdit_isite_2.text())
        else:
            if float(self.lineEdit_isite_2.text())<float(self.lineEdit_sitelb_2.text()) or float(self.lineEdit_isite_2.text())>float(self.lineEdit_siteub_2.text()):
                QMessageBox.information(None, "warning", "The initial guess of sites should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)
            site = (float(self.lineEdit_sitelb_2.text()), float(self.lineEdit_siteub_2.text()))
        if self.checkBox_c1.isChecked() == True:
            c1 = float(self.lineEdit_ic1.text())
        else:
            if float(self.lineEdit_ic1.text())<float(self.lineEdit_ic1lb.text()) or float(self.lineEdit_ic1.text())>float(self.lineEdit_ic1ub.text()):
                QMessageBox.information(None, "warning", "The initial guess of C1 should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)
            c1 = (float(self.lineEdit_ic1lb.text()), float(self.lineEdit_ic1ub.text()))
        if self.checkBox_c2.isChecked() == True:
            c2 = float(self.lineEdit_ic2.text())
        else:
            if float(self.lineEdit_ic2.text())<float(self.lineEdit_ic2lb.text()) or float(self.lineEdit_ic2.text())>float(self.lineEdit_ic2ub.text()):
                QMessageBox.information(None, "warning", "The initial guess of C2 should be within the bounds",
                                    QMessageBox.Yes | QMessageBox.No)
            c2 = (float(self.lineEdit_ic2lb.text()), float(self.lineEdit_ic2ub.text()))
        surface_formula = self.lineEdit_sformula.text()
        surface_formula = surface_formula[0].upper() + surface_formula[1:]
        tem_sp.add_surface(surfacename=current_sname, surface_ms=surface_formula,
                           mass=self.lineEdit_smass_2.text(),
                           sites=site, area=self.lineEdit_sarea_2.text(), c1=c1, c2=c2,
                           sites_initial=float(self.lineEdit_isite_2.text()),
                           c1_initial=float(self.lineEdit_ic1.text()), c2_initial=float(self.lineEdit_ic2.text()))
        return tem_sp

    def update_surface(self):
        sp_name = []
        for obj in self.opad:
            sp_name.append(obj.surface_name)
        current_sname = self.lineEdit_sname_2.text().strip().capitalize()
        # avoid input a blank space as surface name
        if current_sname != "":
            if sp_name.count(current_sname) == 0:
                self.opad.append(self.add_surface2())

            else:
                self.opad.pop(sp_name.index(current_sname))
                self.opad.append(self.add_surface2())

    def del_surf(self):
        current_sname = self.lineEdit_sname_2.text().strip().capitalize()
        for i in range(0, len(self.opad)):
            if self.opad[i].surface_name == current_sname:
                self.opad.pop(i)

    def add_reaction(self):
        reaction = self.lineEdit_reaction.text().strip()
        sp_name = []
        for obj in self.opad:
            sp_name.append(obj.surface_name)
        for name in sp_name:
            if reaction.find(name) != -1:
                if self.checkBox_logk.isChecked() == True:
                    logk = float(self.lineEdit_ik.text())
                else:
                    if float(self.lineEdit_ik.text()) < float(self.lineEdit_iklb.text()) or float(self.lineEdit_ik.text()) > float(self.lineEdit_ikub.text()):
                        QMessageBox.information(None, "warning", "The initial guess of k should be within the bounds",
                                                QMessageBox.Yes | QMessageBox.No)
                    logk = (float(self.lineEdit_iklb.text()), float(self.lineEdit_ikub.text()))
                if self.checkBox_z1.isChecked() == True:
                    z1 = float(self.lineEdit_iz1.text())
                else:
                    if float(self.lineEdit_iz1.text()) < float(self.lineEdit_iz1lb.text()) or float(self.lineEdit_iz1.text()) > float(self.lineEdit_iz1ub.text()):
                        QMessageBox.information(None, "warning", "The initial guess of z1 should be within the bounds",
                                                QMessageBox.Yes | QMessageBox.No)
                    z1 = (float(self.lineEdit_iz1lb.text()), float(self.lineEdit_iz1ub.text()))
                if self.comboBox_charge.currentIndex() == 0:
                    z0d = True
                else:
                    z0d = False
                self.opad[sp_name.index(name)].add_reactions(reactions=reaction, k=logk, z0d=z0d, z1=z1,
                                                             ztotal=float(self.lineEdit_totalz.text()),
                                                             k_initial=float(self.lineEdit_ik.text()),
                                                             z1_initial=float(self.lineEdit_iz1.text()))
                break
        self.show_surface2()

    def del_reaction(self):
        reaction = self.lineEdit_reaction.text().strip()
        for obj in self.opad:
            for rec in list(obj.surface_reactions.keys()):
                if rec == reaction:
                    del obj.surface_reactions[rec]
                    # break
        self.show_surface2()

    def show_surface2(self):
        surface_reaction = ""
        if self.actionEnabled.isChecked() == True:
            surface_reaction += "The surface will equilibrate with a solution before titration ( pH: " + str(
                self.surf_eq[0]) + ", " \
                                + "IS:" + str(self.surf_eq[1]) + ")\n"
        for obj in self.opad:
            surface_reaction += obj.surface_name + "\n"
            if self.comboBox_mdl_2.currentText() == "CCM":
                surface_reaction += str(obj.surface_sites) + " ccm: " + str(obj.surface_C1) + "\n"
            elif self.comboBox_mdl_2.currentText() == "CDMUSIC":
                surface_reaction += str(obj.surface_sites) + " c1: " + str(obj.surface_C1) + " " + \
                                    " c2: " + str(obj.surface_C2) + "\n"
            else:
                surface_reaction += str(obj.surface_sites) + "\n"
            for react in obj.surface_reactions.keys():
                surface_reaction += react + "\n"
                surface_reaction += "\t" + "log_k: " + str(obj.surface_reactions[react][0]) + "\n"
                if self.comboBox_mdl_2.currentText() == "CDMUSIC":
                    if obj.surface_reactions[react][2] == True:
                        location = "z0+z1"
                    else:
                        location = "z1+zd"
                    surface_reaction += "\t" + "z1: " + str(
                        obj.surface_reactions[react][1]) + " location:" + location + " " + str(
                        obj.surface_reactions[react][3]) + "\n"
        self.textEdit_sf_2.setText(surface_reaction)

    def clear_all(self):
        self.opad.clear()
        self.show_surface2()

    def advanced_opt(self):
        try:
            self.config_file.update_config_file([self.data_folder, self.database_folder, self.output_folder])
            task_name = QInputDialog.getText(None, "Task name", "Input here")[0]
            num_process = min([int(self.lineEdit_cycle_2.text(),multiprocessing.cpu_count())])
            problem = mc.Adsorption(self.comboBox_mdl_2.currentText())
            if self.multi_is_ad == False:
                Na = [float(self.lineEdit_cs_2.text())]
            elif self.multi_is_ad == True:
                Na = list(self.mix_data_ad.groups.keys())
            initial_ph = float(self.lineEdit_ph_4.text())
            initial_volume = float(self.lineEdit_ph_5.text())
            metal_name = self.lineEdit_reactant.text()
            if metal_name.strip() == "":
                metal = {}
            else:
                metal_amounts = float(self.lineEdit_moles.text())
                metal = {metal_name: metal_amounts}
            target_com = self.lineEdit_output.text()
            problem.species_definition(self.database, None)
            problem.initial_solution(Na, initial_pH=initial_ph, cation=self.lineEdit_cation.text(),
                                     anion=self.lineEdit_anion.text(),
                                     metal=metal)
            problem.selected_output(output={self.comboBox.currentText(): target_com})
            problem.set_type_acid(type_acid=self.comboBox_ad_2.currentText(),
                                  type_base=self.comboBox_bs_2.currentText())
            for items in self.opad:
                problem.add_surface(items)
            if self.checkBox.isChecked() == True:
                if self.radioButton_fx_2.isChecked() == True:
                    type_solution = "fix_pH"
                    problem.mix_solution(type_solution=type_solution, base_pH=float(self.lineEdit_base_2.text()),
                                         acid_pH=float(self.lineEdit_acid_2.text()))
                elif self.radioButton_ds_2.isChecked() == True:
                    type_solution = "dissolution"
                    problem.mix_solution(type_solution=type_solution, base_mass=float(self.lineEdit_base_2.text()),
                                         acid_mass=float(self.lineEdit_acid_2.text()))
                if self.actionEnabled.isChecked() == True and self.surf_eq != None:
                    problem.equilibrate_solution(self.surf_eq[1], self.surf_eq[0])
                problem.mix_action(initial_volume=initial_volume, mix_volume=self.mix_data_ad)
                problem.get_bounds()
                self.work2 = WorkThreadAdvanced()
                self.pushButton_opt_2.setEnabled(False)
                self.comboBox_mdl_2.setEnabled(False)
                self.work2.set_pa(problem, self.ph_res_ad, int(self.lineEdit_iter_2.text()),
                                  int(self.lineEdit_temp_2.text()), mix=0, method=self.method_selected,
                                  process_num=num_process,task=task_name)
                self.work2.signals.connect(self.display_results2)
                self.work2.start()
            else:
                sep_ph = len(Na) * [float(self.lineEdit_base_2.text())]
                if self.checkBox_7.isChecked() == True:
                    mix = 2
                else:
                    mix = 1
                    problem.eq_ph(ph_list=self.mix_data_ad, eq_phase=self.textEdit.toPlainText(), ph_sep=sep_ph,
                                  auto_p=False)
                problem.get_bounds()
                self.work2 = WorkThreadAdvanced()
                self.pushButton_opt_2.setEnabled(False)
                self.comboBox_mdl_2.setEnabled(False)
                self.work2.set_pa(problem, self.ph_res_ad, int(self.lineEdit_iter_2.text()),
                                  int(self.lineEdit_temp_2.text()),
                                  mix=mix, ph_list=self.mix_data_ad, eq=self.textEdit.toPlainText(),
                                  method=self.method_selected, process_num=num_process,task=task_name)
                self.work2.signals.connect(self.display_results2)
                self.work2.start()
            self.pushButton_stp_2.setEnabled(True)
        except Exception as e:
            write_log(str(e), self.output_folder)
            self.pushButton_opt_2.setEnabled(True)
            self.comboBox_mdl_2.setEnabled(True)

    def display_results2(self, ssss):
        self.pushButton_opt_2.setEnabled(True)
        self.comboBox_mdl_2.setEnabled(True)
        self.pushButton_stp_2.setEnabled(False)
        if ssss["eva"] < int(self.lineEdit_iter2.text()) and self.method_selected == "Differential evolution":
            QMessageBox.information(None, "warning", "The iterations of DE method is rather few, please rerun or change some settings",
                                   QMessageBox.Yes | QMessageBox.No)
        if ssss["successful"] == True:
            log_temp = self.comboBox_mdl_2.currentText()
            self.textEdit_res_2.append(ssss["Task"]+'\n'+ssss["eva"] + "\n" + ssss["time"] + "\n")
            log_temp += ssss["surface"]
            write_log(ssss["Task"]+'\n'+ssss["eva"] + log_temp + "\n" + ssss["time"], self.output_folder)
            write_results(self.ph_res_ad, ssss["model"],ssss["speciation"], self.output_folder)
            self.plot_res(ssss["model"], ssss["type"], view=True)
        else:
            self.textEdit_res_2.append(ssss["Task"]+'\n'+ssss["error"] + "\n")
            write_log(ssss["Task"]+'\n'+ssss["error"], self.output_folder)

    def stop_thread2(self):
        self.work2.terminate()
        write_log("Terminated by user", self.output_folder)
        self.pushButton_stp_2.setEnabled(False)
        self.pushButton_opt_2.setEnabled(True)
        self.comboBox_mdl_2.setEnabled(True)

    def dual_annealing(self):
        self.actiondifferential_evolution.setChecked(False)
        self.actionDual_annealing.setChecked(True)
        self.actionnelder_mead.setChecked(False)
        self.method_selected = self.actionDual_annealing.text()
        self.lineEdit_cycle_2.setEnabled(False)
        self.lineEdit_cycle.setEnabled(False)

    def differential_evolution(self):
        self.actionDual_annealing.setChecked(False)
        self.actiondifferential_evolution.setChecked(True)
        self.actionnelder_mead.setChecked(False)
        self.method_selected = self.actiondifferential_evolution.text()
        self.lineEdit_cycle_2.setEnabled(True)
        self.lineEdit_cycle.setEnabled(True)

    def nelder_mead(self):
        self.actionnelder_mead.setChecked(True)
        self.actionDual_annealing.setChecked(False)
        self.actiondifferential_evolution.setChecked(False)
        self.method_selected=self.actionnelder_mead.text()
        self.lineEdit_cycle_2.setEnabled(False)
        self.lineEdit_cycle.setEnabled(False)

    def label_change_2(self):
        if self.checkBox.isChecked() and self.radioButton_ds_2.isChecked():
            self.label_13.setText("mol/L")
            self.label_16.setText("mol/L")
        elif self.checkBox.isChecked() and self.radioButton_fx_2.isChecked():
            self.label_13.setText("pH value")
            self.label_16.setText("pH value")
        elif self.checkBox.isChecked() == False:
            self.label_13.setText("Sep pH")
        else:
            self.label_13.setText("mol/L")
            self.label_16.setText("mol/L")

    def label_change_1(self):

        if self.radioButton_ds.isChecked():
            self.label_12.setText("mol/L")
            self.label_15.setText("mol/L")
        elif self.radioButton_fx.isChecked():
            self.label_12.setText("pH value")
            self.label_15.setText("pH value")
        else:
            self.label_12.setText("mol/L")
            self.label_15.setText("mol/L")

    def set_database_folder(self):
        self.database_folder = QFileDialog.getExistingDirectory(None, "Open database", dir=self.database_folder)

    def set_data_folder(self):
        self.data_folder = QFileDialog.getExistingDirectory(None, "Open data", dir=self.data_folder)

    def set_output_folder(self):
        self.output_folder = QFileDialog.getExistingDirectory(None, "Output to:", dir=self.output_folder)

    def enable_surf_eq(self):
        if self.stackedWidget.currentIndex() == 2 and self.checkBox.isChecked() == False:
            QMessageBox.information(None, "warning", "This function is ony valid for titration",
                                    QMessageBox.Yes | QMessageBox.No)
            self.disable_surf_eq()
        else:
            self.actionEnabled.setChecked(True)
            self.actionDisabled.setChecked(False)
            ph, ok1 = QInputDialog.getDouble(None, "Input pH", "pH: 0-14", decimals=3)
            surf_eq_prep = []
            if ok1:
                if ph >= 0 and ph <= 14:
                    surf_eq_prep.append(ph)
                    ionic_strength, ok2 = QInputDialog.getDouble(None, "Input IS", "IS (mol/L)", decimals=2)
                    if ok2:
                        surf_eq_prep.append(ionic_strength)
                        self.surf_eq = surf_eq_prep
                    else:
                        self.disable_surf_eq()
                        QMessageBox.information(None, "warning", "Input error, try again",
                                                QMessageBox.Yes | QMessageBox.No)
                else:
                    self.disable_surf_eq()
                    QMessageBox.information(None, "warning", "pH should be 1-14",
                                            QMessageBox.Yes | QMessageBox.No)

    def disable_surf_eq(self):
        self.surf_eq = None
        self.actionEnabled.setChecked(False)
        self.actionDisabled.setChecked(True)


class WorkThreadAdvanced(QThread):
    signals = Signal(dict)

    def __int__(self):
        super(WorkThreadAdvanced, self).__init__()

    def set_pa(self, p1, p2, max_t, T, mix, ph_list=None, eq=None, method="Differential evolution", process_num=1,task=None):
        self.p1 = p1
        self.p2 = p2
        self.max_t = max_t
        self.T = T
        self.mix_or_eq = mix  # 0:mix 1: eq 2: auto_eq
        self.msg = {}
        # self.sep_ph =sep_ph #ph separate point
        self.eq = eq  # extra equilibrium phase in text
        self.ph_list = ph_list  # ph list for equilibrium
        self.method = method
        self.processes = process_num
        self.task_name=task

    def run(self):
        # args for proto_fun is exp_data,titration:Adsorption,mix=ture
        # args for advanced_fun is exp_data, titration:Adsorption,mix=False
        # args for advanced_fun_auto is exp_data,ph_list,eq_phase, titration:Adsorption,mix=False
        problem_type = False
        auto_ph = False
        try:
            if self.mix_or_eq == 0:
                mix = True
                problem_type = True

                fix_para = (self.p2, self.p1, mix)
            elif self.mix_or_eq == 1:  # no auto calculate, use given pH value
                mix = False

                fix_para = (self.p2, self.p1, mix)
            elif self.mix_or_eq == 2:  # automatically calculate pH for each parameters
                mix = False
                auto_ph = True
                fix_para = (self.p2, self.ph_list, self.eq, self.p1, mix)
            st_eva_t = time.time()
            results = mc.optimize_problem(self.mix_or_eq, method=self.method, x0=np.array(self.p1.initial_guess),
                                          bounds=self.p1.bounds, maxiter=self.max_t, core=self.processes, t=self.T,
                                          extra_para=fix_para)
            ed_eva_t = time.time()
            res_str = ""

            eva = mc.advanced_evaluation(exp_data=self.p2, titration=self.p1, results=results, mix=mix, eq=self.eq,
                                         ph_list=self.ph_list, auto_p=auto_ph)
            res_str += "Optimized parameters: "
            for x in results.x:
                res_str += str(x) + "  "
            res_str += "\n" + "R2" + "\t" + "adj. R2" + "\t" + "BIC" + "\t" + "RMSE" + "\t" + "Evaluations" + "\n"
            for y in eva[0:3]:
                res_str += "{:.5f}".format(y) + "\t"
            res_str += "{:.3e}".format(eva[3]) + "\t" + str(eva[4])
            # write_results(self.p2, eva[4],self.output_folder)
            self.msg["Task"]="Task: "+self.task_name
            self.msg["successful"] = True
            self.msg["eva"] = res_str + "\n"
            self.msg["model"] = eva[5].tolist()
            self.msg["surface"] = eva[6]
            self.msg["type"] = problem_type
            self.msg["time"] = "Time: {:.2f} s".format(ed_eva_t - st_eva_t)
            self.msg["speciation"]=eva[7]
            self.msg["iterations"] = eva[4]
            self.signals.emit(self.msg)
        except Exception as e:
            self.msg["Task"] = self.task_name
            self.msg["successful"] = False
            self.msg["error"] = str(e)
            self.signals.emit(self.msg)


class PandasModel(QAbstractTableModel):

    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])

class ConfigFile:
    def __init__(self):
        self.data_directory = None
        self.database_directory = None
        self.output_directory = None
        self.install_path = os.path.split(os.path.realpath(__file__))[0]
        self.config_file = os.path.join(self.install_path, "config")
        # print(self.config_file)
    def create_config_file(self):
        with open(self.config_file,"w") as f:
            f.write(os.getcwd() + "\n")
            f.write(os.getcwd() + "\n")
            f.write(os.getcwd() + "\n")

    def load_config_file(self):
        # check the config file in the folder
        # create the config file if not exists
        # print(os.path.isfile(self.config_file))
        if not os.path.isfile(self.config_file):
            self.create_config_file()
        with open(self.config_file, "r") as f:
            config_content = f.readlines()

        #check the number of lines in the file, must be 3
        if len(config_content) != 3:
            self.create_config_file()
            with open(self.config_file, "r") as f:
                config_content = f.readlines()

        # data/work directory, database directory, and output directory
        for i in range(0,3):
            if not os.path.isdir(config_content[i].strip()):
                config_content[i] = os.getcwd()
        self.data_directory = config_content[0].strip()
        self.database_directory = config_content[1].strip()
        self.output_directory = config_content[2].strip()


    def update_config_file(self,path_list:list):
        # print(path_list)
        with open(self.config_file,"w") as f:
            f.write(path_list[0]+"\n")
            f.write(path_list[1]+"\n")
            f.write(path_list[2]+"\n")


def write_log(log_info: str, output_path: str):
    with open(os.path.join(output_path, "phreefit_log.txt"), "a") as f:
        f.write("\n" + time.ctime() + "\n")
        f.write(log_info + "\n")


def write_results(exp_data, model_res, speciation, output_path: str):
    with open(os.path.join(output_path, "phreefit_results.txt"), "a") as f2:
        f2.write("\n" + time.ctime() + "\n")
        f2.write("Experimental data" + "\t" + "Modeled data"+"\n")
        for i in range(0, len(exp_data)):
            f2.write(str(exp_data[i]) + "\t")
            f2.write(str(model_res[i]) + "\n")
        f2.write("Surface Speciation:" + "\n")
        for sps in np.array(speciation,dtype=str):
            f2.write("\t".join(sps[1:])+"\n")


class MyWindow(QMainWindow):
    def closeEvent(self,event):
        result = QMessageBox.question(None,"Confirm Exit...","Are you sure you want to exit ?",
                                      QMessageBox.Yes| QMessageBox.No,QMessageBox.No)

        if result == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    import sys

    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    MainWindow = MyWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
