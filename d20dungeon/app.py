import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from random import randint
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
# app.jinja_env.filters["d20"] = d20

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///d20tables.db")

# START ____user management and log in/out etc. section____ START
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        username = request.form.get("username")
        confirmation = request.form.get("confirmation")
        password = request.form.get("password")
        player_name = request.form.get("player_name")

        if not player_name:
            return apology("Please provide a valid playername")
        if not username:
            return apology("Please provide a valid username")
        if not password:
            return apology("Please provide a valid password")
        if not confirmation:
            return apology("Please provide a confirmation of your password")
        if password != confirmation:
            return apology("Passwords do not match")
        if len(rows) != 0:
            return apology("this username already exists")

        elif len(rows) == 0:
            password_hash = generate_password_hash(confirmation)

            try:
                db.execute("INSERT INTO users (username, hash, player_name) VALUES(?,?,?)", username, password_hash, player_name)
            except:
                return apology("Username is already taken please try another")

            return redirect("/")


@app.route("/updpass", methods=["GET", "POST"])
@login_required
def update_password():
    """update password"""
    if request.method == "GET":
        return render_template("updpass.html")
    else:

        oldpassword = request.form.get("old")

        user_id = session["user_id"]
        user_db = db.execute("SELECT hash FROM users WHERE id = :id", id=user_id)
        new_password = request.form.get("new-password")
        new_confirmation = request.form.get("new-confirmation")

        if not check_password_hash(user_db[0]["hash"], oldpassword):
            return apology("Incorrect password")
        if not new_password:
            return apology("Please provide a valid password")
        if not new_confirmation:
            return apology("Please provide a confirmation of your password")

        if new_confirmation != new_password:
            return apology("Passwords do not match")
        new_password_hash = generate_password_hash(new_confirmation)

# just create another hash and add that to the db for the user.
        try:
            db.execute("UPDATE users SET hash = ? WHERE ?", new_password_hash, user_id)
            flash("Your Password has been updated")
        except:
            return apology("We could not update your password")

    return redirect("/")
# END ____user management and log in/out etc. section____ END

# Front page nav
@app.route("/")
@login_required
def index():
    """Show front page data"""

    user_id = session["user_id"]
    player_name_db = db.execute("SELECT player_name FROM users WHERE id = ?", user_id)
    player_name = player_name_db[0]["player_name"]
    return render_template("index.html", player_name=player_name)

# History
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Show history of all battles"""

    user_id = session["user_id"]
    player_name_db = db.execute("SELECT player_name FROM users WHERE id = ?", user_id)
    player_name = player_name_db[0]["player_name"]
    battle_history = db.execute("SELECT * FROM battle_history WHERE id = ?", user_id)

    return render_template("history.html", battle_history=battle_history, player_name=player_name)


# Playable Characters page
@app.route("/characters", methods=["GET", "POST"])
@login_required
def characters():
    """Show all playable characters"""

    user_id = session["user_id"]
    player_name = db.execute("SELECT player_name FROM users WHERE id = ?", user_id)[0]["player_name"]
    characters = db.execute("SELECT * FROM characters")

    return render_template("characters.html", characters=characters, player_name=player_name)

# Fightable Monsters page
@app.route("/monsters", methods=["GET", "POST"])
@login_required
def monsters():
    """Show all fightable monsters"""
 # reminder make for loop in carousel for additional characters and images, will have to save image name too probably and can call that specifically for each
    user_id = session["user_id"]
    player_name = db.execute("SELECT player_name FROM users WHERE id = ?", user_id)[0]["player_name"]
    monsters = db.execute("SELECT * FROM monsters")

    return render_template("monsters.html", monster=monsters, player_name=player_name)

# START ___Battle sequence___ START

# !!TODO reminder to make random roller D20 in helpers
# select Character - show stats below carousel - have a form at the bottom for selecting and have that add to the template
# reminder to carry along battle ID for each step - might have to be a helper function maybe? both clear and retain battle id across
@app.route("/character_choice", methods=["GET", "POST"])
@login_required
def battle_seq1():
    """start battle sequence - choose your character"""
    if request.method == "GET":
        user_id = session["user_id"]
        db.execute("DELETE FROM temp_battle WHERE id = ?", user_id)
        characters = db.execute("SELECT * FROM characters")
        return render_template("character_choice.html", characters=characters)
    else:
        user_id = session["user_id"]
        player_name = db.execute("SELECT player_name FROM users WHERE id = ?", user_id)[0]["player_name"]
        character = request.form.get("character_select")
        character_choice_db = db.execute("SELECT * FROM characters WHERE name = ?", character)
        empty_table = db.execute("SELECT * FROM temp_battle WHERE id = ?", user_id)
        if not empty_table:
            db.execute("INSERT INTO temp_battle (player_name, character_name, character_hit_points, character_ac, character_attack_mod, character_damage_mod, character_image_url,id) VALUES (?,?,?,?,?,?,?,?)",
                       player_name, character_choice_db[0]["name"], character_choice_db[0]["hit_points"], character_choice_db[0]["ac"], character_choice_db[0]["attack_mod"], character_choice_db[0]["damage_mod"], character_choice_db[0]["image_url"],user_id)
        else:
            db.execute("UPDATE temp_battle SET player_name = :pname, character_name = :cname, character_hit_points = :chp, character_ac = :cac, character_attack_mod = :cam, character_damage_mod = :cdm, character_image_url = :curl, id = :id",
                       pname=player_name, cname=character_choice_db[0]["name"], chp=character_choice_db[0]["hit_points"], cac=character_choice_db[0]["ac"], cam=character_choice_db[0]["attack_mod"], cdm=character_choice_db[0]["damage_mod"], curl=character_choice_db[0]["image_url"], id=user_id)
        monsters = db.execute("SELECT * FROM monsters")
    return render_template("monsters_choice.html", player_name=player_name, monsters=monsters)

 # !!TODO select monster - can redupe the monster page - add battle button at botton - show stats below carousel
@app.route("/monster_choice", methods=["GET", "POST"])
@login_required
def battle_seq2():
    """start battle sequence - choose the monster """
    if request.method == "POST":
        user_id = session["user_id"]
        monster = request.form.get("monster_select")
        monster_choice_db = db.execute("SELECT * FROM monsters WHERE name = ?", monster)
        db.execute("UPDATE temp_battle SET monster_name = :mname, monster_hit_points = :mhp, monster_ac = :mac, monster_attack_mod = :mam, monster_damage_mod = :mdm, monster_image_url = :murl WHERE id = :id",
                   mname=monster_choice_db[0]["name"], mhp=monster_choice_db[0]["hit_points"], mac=monster_choice_db[0]["ac"], mam=monster_choice_db[0]["attack_mod"], mdm=monster_choice_db[0]["damage_mod"], murl=monster_choice_db[0]["image_url"], id=user_id)
        monsters = db.execute("SELECT * FROM monsters")
        temp_battle_db = db.execute("SELECT * FROM temp_battle WHERE id = ?", user_id)
        return render_template("face_off.html", temp_battle = temp_battle_db, monsters=monsters, monster=monster_choice_db)
    else:
        user_id = session["user_id"]
        temp_battle_db = db.execute("SELECT * FROM temp_battle WHERE id = ?", user_id)
        return render_template("battle_ground.html", temp_battle = temp_battle_db)

@app.route("/battle_ground", methods=["GET", "POST"])
@login_required
def battle_seq3():
    """start battle sequence - choose the monster """
    user_id = session["user_id"]
    temp_battle_db1 = db.execute("SELECT * FROM temp_battle WHERE id = ?", user_id)
    if request.method == "POST":
        user_id = session["user_id"]
        temp_battle_db3 = db.execute("SELECT * FROM temp_battle WHERE id = ?", user_id)
        player_roll = 0
        player_roll = randint(1,20)
        monster_ac = temp_battle_db3[0]["monster_ac"]
        player_att_mod = temp_battle_db3[0]["character_attack_mod"]
        total_player_attack = player_att_mod + player_roll
        db.execute("UPDATE temp_battle SET player_roll = :pr WHERE id = :id", pr=player_roll, id=user_id)
        # we miss
        if monster_ac > total_player_attack:
            flash("You attacked and missed!")
            # monster roll
            monster_roll = 0
            monster_roll = randint(1,20)
            character_ac = temp_battle_db3[0]["character_ac"]
            monster_att_mod = temp_battle_db3[0]["monster_attack_mod"]
            total_monster_attack = monster_att_mod + monster_roll
            db.execute("UPDATE temp_battle SET monster_roll= :mr WHERE id = :id", mr=monster_roll, id=user_id)
            # monster miss
            if character_ac > total_monster_attack:
                flash("the monster missed! Roll Again!")
                return render_template("battle_ground.html", temp_battle=temp_battle_db3 )
            # monster hit
            elif character_ac <= total_monster_attack:
                hit_player = temp_battle_db3[0]["monster_damage_mod"]
                character_hp_update = temp_battle_db3[0]["monster_hit_points"]-hit_player
                monster_damage_dealt_update = temp_battle_db3[0]["monster_damage_dealt"]+hit_player
                db.execute("UPDATE temp_battle SET character_hit_points= :chp, monster_damage_dealt = :mdd WHERE id = :id", chp=character_hp_update, mdd=monster_damage_dealt_update, id=user_id)
                character_hp_db = db.execute("SELECT character_hit_points FROM temp_battle WHERE id = ?", user_id)[0]["character_hit_points"]
                character_hp = int(character_hp_db)
                # they kill first - end game
                if character_hp <= 0:
                    db.execute ("UPDATE temp_battle SET winner = :winner WHERE id = :id", winner=temp_battle_db3[0]["monster_name"], id=user_id)
                    flash("You have been vanquished by the Monster!")
                    return upd_battle_history()
                # character not dead yet
                else:
                    flash("The monster syncs a mighty blow, but you are not dead yet! Roll again!")
                    return render_template("battle_ground.html", temp_battle=temp_battle_db3 )
        # we hit
        elif monster_ac <= total_player_attack:
            hit_monster = temp_battle_db3[0]["character_damage_mod"]
            monster_hp_update = temp_battle_db3[0]["monster_hit_points"] - hit_monster
            player_damage_dealt_update = temp_battle_db3[0]["player_damage_dealt"] + hit_monster
            db.execute("UPDATE temp_battle SET  monster_hit_points = :mhp, player_damage_dealt = :pdd WHERE id = :id", mhp=monster_hp_update, pdd=player_damage_dealt_update, id=user_id)
            monster_hp_db = db.execute("SELECT monster_hit_points FROM temp_battle WHERE id = ?", user_id)[0]["monster_hit_points"]
            monster_hp = int(monster_hp_db)
            # we kill first - end game
            if monster_hp <= 0:
                db.execute("UPDATE temp_battle SET winner = :w WHERE id = :id", w=temp_battle_db3[0]["player_name"], id=user_id)
                flash("The Player has vanquished his foe!")
                return upd_battle_history()
            else:
                flash("We have hit the monster, but the battle is not won yet!")
                # monster roll
                monster_roll = 0
                monster_roll = randint(1,20)
                character_ac = temp_battle_db3[0]["character_ac"]
                monster_att_mod = temp_battle_db3[0]["monster_attack_mod"]
                total_monster_attack = monster_att_mod + monster_roll
                db.execute("UPDATE temp_battle SET monster_roll= :mr WHERE id = :id", mr=monster_roll, id=user_id)
                # monster miss
                if character_ac > total_monster_attack:
                    flash("the monster missed! Roll Again!")
                    return render_template("battle_ground.html", temp_battle=temp_battle_db3 )
                # monster hit
                elif character_ac <= total_monster_attack:
                    hit_player = temp_battle_db3[0]["monster_damage_mod"]
                    character_hp_update = temp_battle_db3[0]["monster_hit_points"]-hit_player
                    monster_damage_dealt_update = temp_battle_db3[0]["monster_damage_dealt"]+hit_player
                    db.execute("UPDATE temp_battle SET character_hit_points = :chp, monster_damage_dealt = :mdd WHERE id = :id", chp=character_hp_update, mdd=monster_damage_dealt_update, id=user_id)
                    character_hp_db = db.execute("SELECT character_hit_points FROM temp_battle WHERE id = ?", user_id)[0]["character_hit_points"]
                    character_hp = int(character_hp_db)
                    # they kill first - end game
                    if character_hp <= 0:
                        db.execute("UPDATE temp_battle SET winner = :w, WHERE id = :id", w=temp_battle_db3[0]["monster_name"], id=user_id)
                        flash("You have been vanquished by the Monster!")
                        return upd_battle_history()
                    # character not dead yet
                    else:
                        flash("The monster syncs a mighty blow, but you are not dead yet! Roll again!")
                        return render_template("battle_ground.html", temp_battle=temp_battle_db3 )

    elif not temp_battle_db1 and request.method == "GET":
        return apology("There is no active battle, Select 'New Battle'")
    return render_template("battle_ground.html", temp_battle=temp_battle_db1 )
# END ___Battle sequence___ END

# insert battle results into battle_history
def upd_battle_history():
    user_id = session["user_id"]
    temp = db.execute("SELECT * FROM temp_battle WHERE id = ?", user_id)
    date = datetime.datetime.now()
    player_name = db.execute("SELECT player_name FROM users WHERE id = ?", user_id)[0]["player_name"]
    db.execute("INSERT INTO battle_history (player_name, winner, monster_name, player_damage, monster_damage, character_name, date, id) VALUES (?,?,?,?,?,?,?,?)",
                player_name, temp[0]["winner"], temp[0]["monster_name"], temp[0]["player_damage_dealt"], temp[0]["monster_damage_dealt"], temp[0]["character_name"], date, user_id)
    db.execute("DELETE FROM temp_battle WHERE id = ?", user_id)
    flash("Battle History Updated!")
    return render_template("index.html")
