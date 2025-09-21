import streamlit as st
import requests

from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd
import os
from datetime import datetime
import pytz
from simple_salesforce import Salesforce
from datetime import datetime as dt
import re
# import time
# import gspread
# from google.oauth2.service_account import Credentials
# from gspread_dataframe import set_with_dataframe
import toml
import streamlit.components.v1 as components

import easyocr
import numpy as np
import cv2
from PIL import Image
import glob

# 固定コンテナコードの始まり
from typing import Literal
from streamlit.components.v1 import html
