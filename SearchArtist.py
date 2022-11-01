import sqlite3

conn = sqlite3.connect('./temp.db')
cur = conn.cursor()

def search_song(UserInput, array):
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
        for i in artist_data:
            print(i)

        print()
        # SongSelection = input('Do you want to select any song - Enter it\'s name: ').strip()


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
        'Select a.name, a.nationality, count(s.sid) from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and a.name = "{}" group by a.name'.format(i))
    row = cur.fetchone()
    result += [[str(j)] + list(row)]
    j += 1

# Printing according to 5 per page
if len(result) == 0:
    print('\nSorry! There is no artist with this name')

else:
    count = 0
    print(str('\n'+'Found ' + str(len(data)) + ' matching results (No., Name, Nationality, Number of Songs)').center(150, '-'))
    for k in result:
        print(k)

        count += 1
        if i == len(result):
            print('This is end of our search result.'.center(150, '-'))
            UserInput = input('Do you want to terminate searching ' + str(len(result) - count) + ' left (Press N) or Select the artist (type it\'snumber)? ').strip()
            if UserInput.lower() == 'n':
                break
            else:
                search_song(UserInput, result)

        elif count % 5 == 0:
            print()
            UserInput = input('Do you want to continue searching ' + str(len(result) - count) + ' left (Press Y/N) or Select the artist (type it\'s number)? ').strip()
            if UserInput.lower() == 'y':
                continue

            elif UserInput.lower() == 'n':
                print()
                print('This is end of our search result.'.center(150, '-'))
                break
            else:
                search_song(UserInput, result)
                break


