import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from helpers import apology, login_required, roll

# Configure application
app = Flask(__name__)

def test():
    """Log user in"""
    test=roll()
    print(test)
    return

