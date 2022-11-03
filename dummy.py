import sqlite3
from datetime import datetime
import os
import time
from getpass import getpass
import sys

# database_name = input("Please provide the database name. Make sure to include extension in file name. ")
conn = sqlite3.connect('temp.db')
cur = conn.cursor()


def start_session(id):
    # Implement Start a session
    print()
    cur.execute("select * from sessions where lower(uid)=?", (id.lower(),))
    data = cur.fetchall()
    id = data[0][0]

    # Storing all the Sno related to given Uid
    store = []
    for row in data:
        store.append(row[1])

    # Finding a unique Sno
    i = 1
    while True:
        if i not in store:
            sno = i
            break
        i = i + 1

    now = datetime.now()
    current_date = now.date()

    query_vals = (id, sno, current_date)
    cur.execute("INSERT INTO sessions (uid, sno, start) VALUES (?,?,?)", query_vals)
    conn.commit()

    return sno

def search_songs_playlists(id):
    while True:
        keyword = input("Please enter one or more keywords to search for, each separated by a single space: ")
        if(keyword.lower()) == '/exit':
            clearTerminal()
            break
        keywords = keyword.split(' ')
        uniqueKeywords = []
        results = []
        counts = {}
        query = "WITH temp as (select pid from playlists where "  # Construct temp table to get matching playlist IDs
        for k in keywords:
            if (k.lower() not in uniqueKeywords):
                uniqueKeywords.append(k.lower())
                query += "(title like '%{}%') or ".format(k)
        query = query[:len(query) - 3] + ") select sid, title, duration, ("  # Get matching songs
        for k in uniqueKeywords:  # get number of keyword matches
            query += "case when title like '%{}%' then 1 else 0 end + ".format(k)
        query = query[:len(query) - 3] + ") as rank, 'Song' from songs where "
        for k in uniqueKeywords:  # construct the WHERE clause
            query += "(title like '%{}%') or ".format(k)
        query =  query[:len(query) - 3] + "union select p.pid, p.title, sum(s.duration) as duration, ("  # Playlists
        for k in uniqueKeywords:  # get number of keyword matches
            query += "case when p.title like '%{}%' then 1 else 0 end + ".format(k)
        query = query[:len(query) - 3] + ") as rank, 'Playlist' from playlists p, plinclude pl, temp t, songs s "
        query += "where p.pid = t.pid and p.pid = pl.pid and pl.sid = s.sid group by p.pid order by rank DESC "

        cur.execute(query)
        data = cur.fetchall()
        i = 1
        for row in data:
            results.append('{}.\t{} ID: {} | Title: {} | Duration: {} seconds'.format(i, row[4], row[0], row[1], row[2]))
            i+=1
        if i > 1:
            # menu = "Please enter one or more keywords to search for, each separated by a single space: "
            # + keyword + "\nTotal number of results: {}".format(i-1)
            print("Total number of results: {}".format(i-1))
            j = 0
            print(*results[j:j+5],sep="\n")
            j += 5
            userInput = input("\nPlease select a row number, or type 'more' to see more results: ").lower()
            done = False
            while done == False:
                if(userInput.lower()) == '/exit':
                    clearTerminal()
                    break
                prompt = "\nUnrecognized input. Please select a row number, or type 'more' to see more results: "
                try:  # User entered a number
                    userInput = int(userInput)-1
                    if (userInput in range(len(data))):
                        done = True
                        song_action(id, data[userInput][0], data[userInput][1], data[userInput][4])
                except ValueError:  # User entered a string
                    if userInput == 'more':
                        print(*results[j:j+5],sep="\n")
                        j += 5
                        prompt = "\nPlease select a row number, or type 'more' to see more results: "

                if done == False: userInput = input(prompt).lower()
        else:  # No results
            print("No matching songs or playlists")


def song_action(uid, selectionID, selectionTitle, songOrPlaylist):
    # Song Action
    if songOrPlaylist == 'Playlist':  # User selected a playlist
        print("Songs in the playlist '{}':".format(selectionTitle))
        cur.execute('''
            SELECT s.sid, s.title, s.duration
            from playlists p, plinclude pl, songs s
            where p.pid = ? and p.pid = pl.pid and pl.sid = s.sid
            ''', (selectionID,))
        data = cur.fetchall()
        i = 1
        for row in data:
            print('{}.\t Song ID: {} | Title: {} | Duration: {} seconds'.format(i, row[0], row[1], row[2]))
            i+=1
        userInput = input("\nPlease select a row number: ").lower()
        done = False
        while done == False:
            if(userInput.lower()) == '/exit':
                clearTerminal()
                break
            try:  # User entered a number
                userInput = int(userInput)-1
                if (userInput in range(len(data))):
                    done = True
                    song_action(uid, data[userInput][0], data[userInput][1], 'Song')
            except ValueError:  # User entered a string
                pass

            if done == False: userInput = input("\nUnrecognized input. Please select a row number, or type 'more' to see more results: ").lower()
    else:  # User selected a song
        clearTerminal()
        print("1. Listen to '{}'".format(selectionTitle) + "\n2. See more information\n3. Add {} to a playlist".format(selectionTitle))
        userInput = input("Please select an action to perform for the song '{}': ".format(selectionTitle))
        done = False
        while done == False:
            if(userInput.lower()) == '/exit':
                clearTerminal()
                break
            prompt = "Unrecognized input. Please select an action to perform for the song '{}': ".format(selectionTitle)
            try:  # User entered a number
                userInput = int(userInput)  # This will throw an error if the input is not a number
                if userInput in range(1,4):
                    done = True
                    if userInput == 1:  # Listen to song
                        cur.execute("SELECT sno from sessions where uid=? and end is null", (uid,))  # Check if user has an active session
                        data = cur.fetchall()
                        if not data:  # No active session
                            print("Could not listen, you do not have an active session!\n")
                        else:
                            sessionNumber = data[0][0]  # This will throw an error if the user does not have an active sesssion
                            # See if we have already listened to this song in this session (if yes, increase cnt, don't insert new entry)
                            cur.execute("SELECT cnt from listen where uid=? and sno=? and sid=?", (uid,sessionNumber,selectionID,))
                            data = cur.fetchall()
                            if not data:  # User has not listen to this song in this session - insert a new row
                                cur.execute("INSERT INTO listen values (?, ?, ?, 1)", (uid, sessionNumber, selectionID,))
                                conn.commit()
                            else:
                                existingCnt = data[0][0]  # Throws an error if this song is not already in this session
                                cur.execute("UPDATE listen set cnt = cnt+1 where uid=? and sno=? and sid=?", (uid, sessionNumber, selectionID,))
                                conn.commit()
                            print("Now listening...\n")
                    elif userInput == 2:  # See more information
                        # Print all artists that performed the song
                        cur.execute("SELECT a.name from perform p, artists a where p.sid = ? and p.aid = a.aid", (selectionID,))
                        artists = cur.fetchall()
                        result = "Artist(s): "
                        for a in artists:
                            result += a[0] + ", "
                        print("\n" + result[:len(result) - 2])
                        
                        # Print id, title and duration of song
                        cur.execute("SELECT * from songs where sid = ?;", (selectionID,))
                        data = cur.fetchall()
                        print('Song ID: {}\nTitle: {}\nDuration: {} seconds'.format(data[0][0], data[0][1], data[0][2]))

                        # Print matching playlists
                        cur.execute("SELECT p.title from playlists p, plinclude pl where pl.sid = ? and pl.pid = p.pid", (selectionID,))
                        playlists = cur.fetchall()
                        result = "Playlist(s): "
                        cnt = 0
                        for p in playlists:
                            result += p[0] + ", "
                            cnt += 1
                        if cnt == 0:
                            print("This song does not appear in any playlists.\n")
                        else:
                            print(result[:len(result) - 2] + "\n")
                    else:  # Add song to a playlist
                        addedToPlaylist = False
                        while addedToPlaylist == False:
                            cur.execute("SELECT * from playlists where uid=?", (uid,))
                            data = cur.fetchall()
                            print('0.\t Choose this option to create a new playlist')
                            i = 1
                            for row in data:
                                print('{}.\t Playlist ID: {} | Playlist Title: {}'.format(i, row[0], row[1]))
                                i+=1
                            userInput = input("\nPlease select a row number: ").lower()
                            done = False
                            while done == False:
                                if(userInput) == '/exit':
                                    clearTerminal()
                                    done = True
                                    addedToPlaylist = True
                                    break
                                try:  # User entered a number
                                    userInput = int(userInput)
                                    if userInput == 0:  # Create new playlist
                                        done = True
                                        cur.execute("SELECT max(pid) from playlists;")
                                        newPID = int(cur.fetchall()[0][0])+1
                                        newPlaylist = input("Please enter the title of your new playlist: ")
                                        cur.execute("INSERT INTO playlists values (?,?,?)", (newPID, newPlaylist, uid,))
                                        conn.commit()
                                        print("Successfully created new playlist.")
                                    elif userInput in range(len(data)+1):
                                        done = True
                                        addedToPlaylist = True
                                        pid = data[userInput-1][0]
                                        cur.execute("SELECT max(sorder) from plinclude where pid=?;", (pid,))
                                        data = cur.fetchall()
                                        try:  # Playlist is empty
                                            newSOrder = int(data[0][0])+1
                                        except:
                                            newSOrder = 1
                                        try:
                                            cur.execute("INSERT INTO plinclude values (?, ?, ?)", (pid, selectionID, newSOrder,))
                                            conn.commit()
                                            print("Successfully added song to playlist!")
                                        except sqlite3.IntegrityError:
                                            print("Error: This song is already in this playlist!\n")
                                except ValueError:  # User entered a string
                                    pass
                                if done == False: userInput = input("\nUnrecognized input. Please select a row number: ").lower()
                else:
                    prompt = "Invalid number entered! Please enter a number between 1 and 3: "
            except ValueError:  # User did not enter a number
                prompt = "Input was not a number! Please enter a valid number between 1 and 3: "
            
            if done == False: userInput = input(prompt)

def search_artists(uid):
    keyword = input('Enter one or more unique keywords to search for an artist\'s name: ').strip()  # Input
    ArrKeyword = keyword.split()  # Splitting keywords into an array
    queried_data = []

    # Fetching name of artists having the inputted keywords
    for i in range(len(ArrKeyword)):
        cur.execute(
            "Select a.name, s.title from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and (s.title like '%{}%' or a.name like '%{}%');".format(
                ArrKeyword[i], ArrKeyword[i]))
        data = cur.fetchall()

        queried_data += data

    artistData = []

    # Adding names of artists into artistData array
    for i in range(len(queried_data)):
        artistData.append(queried_data[i][0])

    # Sorting the data acc to number of matching keywords
    artistData = sorted(artistData, key=artistData.count, reverse=True)

    # Removing duplicate entries after sorting
    artistData = list(dict.fromkeys((artistData)))

    # Fetching name, nationality & count of songs for a given set of artists using artistsData
    result = []
    j = 1
    for i in artistData:
        cur.execute(
            'Select a.name, a.nationality, count(s.sid) from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and a.name = "{}" group by a.name'.format(
                i))
        row = cur.fetchone()
        result += [[str(j)] + list(row)]
        j += 1

    # Printing according to 5 per page
    if len(result) == 0:
        print('\nSorry! There is no artist with this name')

    else:
        count = 0
        print(str('\n' + 'Found ' + str(
            len(result)) + ' matching results (No., Name, Nationality, Number of Songs)').center(150, '-'))
        for k in result:
            print(k)

            count += 1
            if i == len(result):
                print('This is end of our search result.'.center(150, '-'))
                UserInput = input('Do you want to terminate searching ' + str(
                    len(result) - count) + ' left (Press N) or Select the artist (type it\'snumber)? ').strip()
                if UserInput.lower() == 'n':
                    break
                else:
                    search_song(UserInput, result)

            elif count % 5 == 0:
                print()
                UserInput = input('Do you want to continue searching ' + str(
                    len(result) - count) + ' left (Press Y/N) or Select the artist (type it\'s number)? ').strip()
                if UserInput.lower() == 'y':
                    continue

                elif UserInput.lower() == 'n':
                    print()
                    print('This is end of our search result.'.center(150, '-'))
                    break
                else:
                    search_song(UserInput, result, uid)
                    break

def search_song(UserInput, array, uid):
    # created for search_artist function to avoid writing duplicate code. This function is not required by assignment schema
    try: int(UserInput)
    except ValueError:
        print('Invalid choice!!')
    else:
        cur.execute("Select s.sid, s.title, s.duration from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and a.name = '{}';".format(array[int(UserInput)-1][1]))
        artist_data = cur.fetchall()

        if len(artist_data) == 0:
            print('Invalid choice! Try again later ')

        print(str('Songs of ' + array[int(UserInput)-1][1] + ' (id, title, duration)').center(150, '-'))
        songs = {}
        for i in artist_data:
            print(i)
            songs[i[1]] = i[0]

        print()
        SongSelection = input('Do you want to select any song - Enter it\'s name: ').strip()

        song_action(uid, songs[SongSelection], SongSelection, 'Song')

def user_session(id):

    # User Session
    menu = "User Session\n1. Start a session\n2. Search for songs and playlists\n3. Search for artists\n4. End the session\n5. Log out\n6. Exit the System"
    while True:
        print(menu)

        user_option = input(str("Please enter an option #: "))
        while(user_option not in ["1", "2", "3", "4","5","6"]):
            clearTerminal()
            print(menu)
            user_option = input(str("Invalid option entered. Please enter an option #: "))

        if user_option == "1":
            returned_sno = start_session(id)

        elif user_option == "2":
            clearTerminal()
            search_songs_playlists(id)

        elif user_option == "3":
            search_artists(id)

        elif user_option == "4":
            now = datetime.now()
            current_date = now.date()
            cur.execute("UPDATE sessions set end = ? where lower(uid) = ? and sno = ?", (current_date, id.lower(), returned_sno))
            conn.commit()
        elif user_option == "5":
            now = datetime.now()
            current_date = now.date()
            cur.execute("UPDATE sessions set end = ? where lower(uid) = ? and end IS NULL", (current_date, id.lower()))
            conn.commit()
            break
        elif user_option == "6":
            now = datetime.now()
            current_date = now.date()
            cur.execute("UPDATE sessions set end = ? where lower(uid) = ? and end IS NULL", (current_date, id.lower()))
            conn.commit()    
            clearTerminal()        
            sys.exit()
        else:
            print("Please enter a valid Option #")

def add_song(id, title, duration):

    # cur.execute("select * from artits")
    # data = cur.fetchall()   
    cur.execute("select * from artists where lower(aid)=?", (id.lower(),))
    data = cur.fetchall()
    id = data[0][0]

    artits_id = input("Please provide the ids of any additional artist who have performed this song separated by space: ")
    cur.execute("select * from songs")
    data = cur.fetchall()
    store = []
    i = 1

    for row in data:
        store.append(row[0])

    while True:
        if i not in store:
            sid = i
            break
        i = i + 1

    artits_list = artits_id.split()
    artits_list.append(id)
    cur.execute("INSERT INTO songs (sid, title, duration) VALUES (?,?,?)", (sid, title, duration))
    conn.commit()

    for aid in artits_list:
        cur.execute("select * from artists where lower(aid) = ?", (aid.lower(), ))
        data = cur.fetchall()
        if not data:
            print("Artit "+ aid + " does not exists in the Database")
        else:
            # To ensure that Iam only using the aid in the case format that it appears in my database.
            cur.execute("select * from artists where lower(aid)=?", (aid.lower(),))
            data = cur.fetchall()
            aid = data[0][0]
            cur.execute("INSERT INTO perform (aid, sid) VALUES (?,?)", (aid, sid))
            conn.commit()

def find_top_fans_and_playlist(artistId):
    # list top 3 users who listen to their songs the longest time
    cur.execute("select uid from (Select l.uid, sum(s.duration*l.cnt) as time from songs s, listen l, perform p where s.sid = l.sid and s.sid = p.sid and p.aid in {} group by l.uid order by time desc limit 3)".format((artistId.lower(), artistId.upper(), artistId.capitalize(), artistId.title())))

    users = cur.fetchall()
    print("Top 3 Users ID who listen to your songs the longest time \n")
    for i in users:
        print(i)

    print("-".center(150, '-'))

    # list top 3 playlists that include the largest number of their songs.
    cur.execute("select pid from (Select pid, count(sid) from plinclude where sid in (Select s.sid from songs s, perform p where s.sid = p.sid and p.aid in {}) group by pid order by count(sid) desc limit 3) ".format((artistId.lower(), artistId.upper(), artistId.capitalize(), artistId.title())))
    playlists = cur.fetchall()
    print("Top 3 Playlists ID that include the largest number of your songs. \n")
    for j in playlists:
        print(j)

def artist_session(id):
    # "Artist Session"
    menu = "Artist Session\n1. Add a Song\n2. Find top 3 fans and Playlists\n3. Log out"

    while True:
        print(menu)
        user_option = input(str("Please enter an option #: "))

        while(user_option not in ["1", "2", "3"]):
            clearTerminal()
            print(menu)
            user_option = input(str("Invalid option entered. Please enter an option #: "))

        if user_option == "1":
            title = input("Please provide the title of the song: ")
            duration = input("Please provide the duration of the song (in seconds): ")
            cur.execute("select * from perform, songs where perform.sid = songs.sid and lower(perform.aid) = ? and lower(title) = ? and duration = ?", (id.lower(), title.lower(), duration))
            data = cur.fetchall()
            

            if not data:
                # we can add a song
                add_song(id, title, duration)
            else:
                response = input("WARNING: Song exists\nPress 1. To reject the Song\nPress 2. To still add it as New Song ")
                if response == "1":
                    clearTerminal()
                elif response == "2":
                    add_song(id, title, duration)
                else:
                    print("Wrong input. Going back to MENU")
                time.sleep(1)
                clearTerminal()
        elif user_option == "2":
            find_top_fans_and_playlist(id)
        elif user_option == "3":
            break

def clearTerminal():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the system terminal to look cleaner

def main():
    while True:
        userfound = False
        artistfound = False

        clearTerminal()  # Clear the system terminal to look cleaner
        id = input("Login Screen: Please enter your ID:  ").strip()
        cur.execute("select name from users where lower(uid)=?", (id.lower(),))
        data = cur.fetchall()

        if not data:
            userfound = False
        else:
            userfound = True
            foundUserName = data[0][0]

        cur.execute("select name from artists where lower(aid)=?", (id.lower(),))
        data = cur.fetchall()

        if not data:
            artistfound = False
        else:
            artistfound = True
            foundArtistName = data[0][0]

        # If the ID exists in both users and artists
        if (artistfound == True and userfound == True):
            print("This ID exists for both a user and an artist")
            print("Press 1 to log in as the user {}: {}".format(id, foundUserName))
            print("Press 2 to log in as the artist {}: {}".format(id, foundArtistName))

            user_option = 0
            user_option = input("\nPlease enter your option: ")

            # TODO Implement the Case-Inssensitive functionality in cur.execute statements
            while (user_option != "1" and user_option != "2"):
                print("\r", end="")
                user_option = input("Invalid option. Please enter either 1 for user or 2 for artist: ").strip()

            userpass = getpass(
                prompt=("Please enter your password (as a" + (" user): " if user_option == "1" else "n artist): ")))
            cur.execute("select {} from {} where {}=? and pwd=?".format(
                "uid" if user_option == "1" else "aid", "users" if user_option == "1" else "artists",
                "uid" if user_option == "1" else "aid"), (id, userpass))
            data = cur.fetchall()

            response = "0"
            count = 0
            while (not data):
                if (count >= 1):
                    response = input("Incorrect Passowrd. Would you like to go back to the Log-in Terminal?\nPress 1. for YES Otherwise press any keyword for NO ")
                    if response == "1":
                        break
                userpass = getpass(prompt="Incorrect password. Please try again: ")
                cur.execute("select {} from {} where {}=? and pwd=?".format(
                    "uid" if user_option == "1" else "aid", "users" if user_option == "1" else "artists",
                    "uid" if user_option == "1" else "aid"), (id, userpass))
                data = cur.fetchall()
                count = count+1
            
            if response != "1":
                print("Log-in Successful! Navigating to main screen...")
                time.sleep(1.2)
                clearTerminal()
                user_session(id) if user_option == "1" else artist_session(id)


        # If the id exists for only the user
        elif (userfound == True and artistfound == False):
            userpass = getpass(prompt="Please enter your password: ")
            cur.execute("select uid from users where lower(uid)=? and pwd=?", (id.lower(), userpass))
            data = cur.fetchall()

            response = "0"
            count = 0
            while (not data):
                if (count >= 1):
                    response = input("Incorrect Passowrd. Would you like to go back to the Log-in Terminal?\nPress 1. for YES Otherwise press any keyword for NO ")
                    if response == "1":
                        break
                userpass = getpass(prompt="Incorrect password was provided. Please try again: ")
                cur.execute("select uid from users where lower(uid)=? and pwd=?", (id.lower(), userpass))
                data = cur.fetchall()
                count = count+1
            else:
                print("Log-in Successful! Navigating to main screen...")
                time.sleep(1.2)
                clearTerminal()
                user_session(id)

        # If the id exists for only the artists
        elif (userfound == False and artistfound == True):
            userpass = getpass(prompt="Please Enter your Password: ")
            cur.execute("select aid from artists where lower(aid)=? and pwd=?", (id.lower(), userpass))
            data = cur.fetchall()

            response = "0"
            count = 0
            while (not data):
                if (count >= 1):
                    response = input("Incorrect Passowrd. Would you like to go back to the Log-in Terminal?\nPress 1. for YES Otherwise press any keyword for NO ")
                    if response == "1":
                        break
                userpass = getpass(prompt="Incorrect password was provided. Please try again: ")
                cur.execute("select aid from artists where lower(aid)=? and pwd=?", (id.lower(), userpass))
                data = cur.fetchall()
                count = count+1
            else:
                print("Log-in Successful! Navigating to main screen...")
                time.sleep(1.2)
                clearTerminal()
                artist_session(id)

        # Invalid Id. Ask for Sign-up
        else:
            print("No valid user or artist ID found. Would you like to sign-up as a new user?")
            user_option = input(str("Press 1 to continue!! \nPress anything else to go back to Log-in Terminal ")).strip()

            if user_option == "1":
                id = input("Please provide a user-id: ").strip()
                cur.execute("select uid from users where lower(uid)=?", (id.lower(),))
                data = cur.fetchall()

                if not data:
                    name = input("Please provide a name: ").strip()
                    password = input("Please provide a Password: ").strip()

                    query_vals = (id, name, password)
                    cur.execute("INSERT INTO users (uid, name, pwd) VALUES (?,?,?)", query_vals)
                    conn.commit()

                    print("Sign-Up Successfull! You are now logged-in")
                    user_session(id)

                else:
                    print("This user-id already exists.")
                    time.sleep(1.2)

# main()
search_artists('u1')