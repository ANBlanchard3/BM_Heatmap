import math
from PIL import Image, ImageDraw, ImageFont
import csv
import os.path
import time

# Load a map just to use as a reference for size
map = Image.open("British_Museum_map_room_numbers-1.png")


# Constants / Parameters
RPerSec = 8 # Scales the amplitude of the heatmap at stops
groupWidthWalking = 20 # approximate pixel width of the group while walking
groupWidthStopping = 50 # approximate pixel size of the group while stopped
Rpath = 10 # Scales the amplitude of the heatmap along paths

# Gaussian Function Definition
a = 1 # Amplitude of the curve is 0-1
b = 0 # center the curve on 0
c = groupWidthWalking/3 # std deviation

i = 0 # path index

# Create a 3D matrix the size of the map to store the amplitude of the heatmap at each pixel for each map. This is necessary because png files cannot store floats.
# The AMatrix is added to the red band of black areas on the map to create the heatmap in rooms
# The BMatrix is subtracted from the green and blue bands of white areas on the map to create the heatmap in stairs, shops, cafes, etc.
# The CMatrix stores only the paths themselves, which can be displayed in green on the heatmap
# The DMatrix is used to create the visitor impact heatmap
AMatrix = [[[0] * 3 for _ in range(map.size[0])] for _ in range(map.size[1])]
BMatrix = [[[255] * 3 for _ in range(map.size[0])] for _ in range(map.size[1])]
CMatrix = [[[0] * 3 for _ in range(map.size[0])] for _ in range(map.size[1])]
DMatrix = [[[0] * 3 for _ in range(map.size[0])] for _ in range(map.size[1])]
allStops = []
allArtifacts = []
heatmaps = []
blackmaps = []

# Initialize the artifact index from a default list of the audio coded objects. Objects in this list can be referenced by their audio tour ID. 
# An artifact is defined as a unique object in the museum that can be visited, and is stored as a list
# The artifact index is a list of lists where each list (artifact) contains the following elements:
# 0: Universal ID (artifacts not in the index are assigned a new ID at runtime)
# 1: Audio Tour ID (if present)
# 2: Name (String)
# 3: Room (String)
# 4: Visits (int, number of times visited by the observed ITGs)
# 5: Average Time (int, Average dwell time in seconds)
# 6: Tags (A dictionary of tags and the number of their occurances at the artifact)
# 7: Comments (List of Strings)
# 8: Position (List of Tuples)
# 9: Floor (int, refers to the map the artifact is on: 1, 2, or 3)
try:
    with open("Unified Artifact Index.csv", newline='', encoding='utf-8-sig') as f:
        print(f"Reading Unified Artifact Index.csv")
        reader = csv.reader(f)
        artifactIndex = list(reader)
        for col in artifactIndex[2:]:
            artifact = []
            artifact.append(col[0])
            artifact.append(col[1])
            artifact.append(col[2])
            artifact.append(col[3])
            artifact.append(int(col[4]))
            artifact.append(int(col[5]))
            artifact.append({"sp": 0, "eng": 0, "deng": 0, "b": 0, "st": 0, "dt": 0, "fa": 0, "bg": 0})
            artifact.append([])
            artifact.append([])
            artifact.append(col[9])
            allArtifacts.append(artifact)

except FileNotFoundError:
    print(f"File Unified Artifact Index.csv not found")
    pass


# Iterate over every path file until no more exist
while os.path.exists(f"path{i+1}.csv"):
    print(f"Generating path {i+1}")
    pathStops = [] # Initialize the list of stops on the path
    pathArtifacts = [] # Initialize the list of artifacts visited on the path

    # Read path positions from csv file
    try:
        with open(f"path{i+1}.csv", newline='', encoding='utf-8-sig') as f:
            print(f"Reading path{i+1}.csv")
            reader = csv.reader(f)
            path = list(reader)

            # initialize variables for the path
            T = 0 # Flag used to keep track of whether the group is travelling or stopped: 0 = dwell, 1 = travel
            seconds = 0 # dwell time in seconds
            name = "" # name of the artifact
            xpos = 0 # x pixel coordinate of the stop
            ypos = 0 # y pixel coordinate of the stop
            floor = 0 # map the stop is on

            for col in path:
                stop = [] # Initialize a new stop

                if(col[5].isnumeric() == True): # If there is a number in the x coordinate column (i.e. the row represents a stop)
                    T = 0 # Set the flag to 0 (dwell)

                    # Convert time to seconds
                    time = col[2].split(':') # Split the time into a list at colons
                    if len(time) == 3: # identify what format the time is in by looking at the length of the resulting list
                        seconds = int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2]) # hh:mm:ss format
                    else:
                        seconds = int(time[0]) * 60 + int(time[1]) # mm:ss format
            
                    name = col[4] # Get the name of the artifact
                    xpos = col[5] # Get the x pixel coordinate of the stop
                    ypos = col[6]  # Get the y pixel coordinate of the stop
                    floor = col[7] # Get the floor of the stop

                    inIndex = False # This flag determines whether the artifact is already in the index (0 = not in index, 1 = in index)
                    alreadyVisited = False 

                    # Names can be recorded with additional information in parentheses for context, which is removed here. 
                    # Stops that are not at specific artifacts should also be placed in parentheses, and they will not be ignored in the artifact index but still considered in the heatmap.
                    if(name.isnumeric() == False): 
                        name = name.split('(')[0].strip() # Remove characters within parentheses from the name

                    # Update arifact in the index if it already exists in the index and is not referred to by an audio guide ID number
                    if(name.isnumeric() == False and name): # The recorded name is not a number and is in the index
                        # Remove characters within parentheses from the name
                        for artifact in allArtifacts: # Iterate through existing artifact names
                            if(artifact[2].strip().lower() == name.strip().lower()): # If the recorded artifact is in the artifact index
                                # Modify the artifact data
                                for artifactName in pathArtifacts:
                                    if(name == artifactName):
                                        alreadyVisited = True
                                        break
                                if(not alreadyVisited):
                                    artifact[4] += 1 # Increment the number of times the artifact has been visited
                                    pathArtifacts.append(name)
                                artifact[5] += seconds # Increment the total time spent at the artifact (average is calculated later)
                                if col[8]: # If there are tags
                                    tags = col[8].split(' ') # Split the tags into a list
                                    for tag in tags:
                                        artifact[6][tag.lower()] += 1 # Increment the number of occurences of each tag
                                if col[9]: # If there is a comment
                                    artifact[7].append(col[9]) # Add the comment to the artifact
                                artifact[8].append([xpos, ypos])
                                if not artifact[9]:
                                    artifact[9] = col[7]
                                
                                print("Artifact " + name + " data updated")
                                inIndex = True
                                break

                    # Add an artifact to the index if it is not already in the index and is not referred to by an audio guide ID number
                    if(name.isnumeric() == False and not inIndex and name): # If the artifact is not in the artifact index, is not a number, and does not include parentheses
                        # Create a new artifact
                        artifact = []
                        artifact.append(len(allArtifacts) + 1) # Create a new universal ID
                        artifact.append("N/A") # No audio tour id
                        artifact.append(name) # Use the recorded name as written
                        artifact.append("uknown") # Placeholder for room
                        artifact.append(1) # Number of times visited is initially 1
                        artifact.append(seconds) # Total time spent at the artifact
                        artifact.append({"sp": 0, "eng": 0, "deng": 0, "b": 0, "st": 0, "dt": 0, "fa": 0, "bg": 0})
                        if col[8]: # If there are tags
                            tags = col[8].split(' ') # Split the tags into a list
                            for tag in tags:
                                artifact[6][tag.lower()] += 1 # Increment the number of occurences of each tag
                        if col[9]: # If there is a comment
                            artifact.append([col[9]]) # Initialize comment list
                        else:
                            artifact.append([]) # Initialize comment list
                        artifact.append([[xpos, ypos]]) # Initialize position list
                        artifact.append(col[7])
                        allArtifacts.append(artifact)
                        print("Added " + name + " to the artifact index")

                    # Update arifact in the index if it already exists in the index and is referred to by an audio guide ID number 
                    # artifacts referred to by audio guide ID number should be initialized in the unified artifact. If they are not, they will not be added, and instead a warning will be printed
                    if(name.isnumeric() == True): # If the recorded name is a number
                        for artifact in allArtifacts: # Iterate through existing artifact names
                            try:
                                if(int(artifact[1]) == int(name)): # If the recorded artifact is in the artifact index
                                    name = artifact[2] # use the name of the artifact
                                    # Modify the artifact data
                                    for artifactName in pathArtifacts:
                                        if(name == artifactName):
                                            alreadyVisited = True
                                            break
                                    if(not alreadyVisited):
                                        artifact[4] += 1 # Increment the number of times the artifact has been visited
                                        pathArtifacts.append(name)
                                    artifact[5] += seconds # Increment the total time spent at the artifact (average is calculated later)
                                    if col[8]: # If there are tags
                                        tags = col[8].split(' ') # Split the tags into a list
                                        for tag in tags:
                                            artifact[6][tag.lower()] += 1 # Increment the number of occurences of each tag
                                    if col[9]: # If there is a comment
                                        artifact[7].append(col[9]) # Add the comment to the artifact
                                    artifact[8].append([xpos, ypos])
                                    if not artifact[9]:
                                        artifact[9] = col[7]
                                    k = 1
                                    print("Artifact " + artifact[2] + " data updated")
                                    break

                            # Warning that an audio guide ID number is not in the unified artifact index
                            except ValueError:
                                print("Artifact number " + name + " is missing from the index") 
                                pass

                # If the row is a dwell with no position designator after a stop, the group has not moved, and the time and any tags and comments are added to the previous stop
                elif(col[3] == "D" and T == 0):
                    # Convert time to seconds
                    time = col[2].split(':')
                    if len(time) == 3:
                        seconds2 = int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2])
                        artifact[5] += seconds2
                        seconds += seconds2
                    else:
                        seconds2 = int(time[0]) * 60 + int(time[1])
                        artifact[5] += seconds2
                        seconds += seconds2
                    if col[8]: # If there are tags, increment the occurances of each tag
                        tags = col[8].split(' ')
                        for tag in tags:
                            artifact[6][tag.lower()] += 1
                    if col[9]: # If there is a comment, add the comment to the artifact
                        artifact[7].append(col[9])
                    print("Artifact " + artifact[2] + " data updated")

                # If the row if a travel with no position designator after a stop, the group has moved, and a stop can be created with complete information
                elif(col[3] == "T" and T == 0):
                    T += 1 # Set the flag to 1 (travel)
                    stop.append(seconds)
                    stop.append(name)
                    stop.append(xpos)
                    stop.append(ypos)
                    stop.append(floor)
                    pathStops.append(stop)
                    allStops.append(pathStops)
                    
    # If the path file is not found, print an error message
    except FileNotFoundError:
        print(f"File path{i+1}.csv not found")
        pass


    # This portion of the script generates the heatmap from the list of stops (not the list of artifacts)
    # i is the iterator for the path or group number and j is the iterator for the map number
    for j in range(3):
        try:
            path = Image.open(f"path{i+1}-{j+1}.png") # Load the path
            print(f"Reading path{i+1}-{j+1}.png")
            map = Image.open(f"British_Museum_map_no_icons-{j+1}.png") # Load a version of the map without icons
            pathSource = path.split()
            mapSource = map.split()

            # Create a mask for the path, split into RGBA bands
            R, G, B, A = 0, 1, 2, 3

            # Creat new R band
            new_R = mapSource[R].copy()
            new_R_data = new_R.load()

            # 55 oppacity mask to isolate a one pixel wide path independent of the width of the path drawn in Inkscape. 
            # This threshold works for a spline drawn with HSLA values of 120, 100, 50, 0, with opacity set to 50% in Inkscape.
            # If these values are changed, the threshold may need to be adjusted by trial and error, modifying this threshold and looking at the resulting mask until a 1 pixel wide path is created.
            mask = pathSource[A].point(lambda i: i > 55 and 255) 
            #mask.save(f"mask{i+1}-{j+1}.png") # If you want to save the mask for debugging

            # generate a list of pixels on the path
            selected_pixels = [(x, y) for y in range(mask.size[1]) for x in range(mask.size[0]) if mask.getpixel((x, y)) == 255]
    
            # If a path is too short, raise an exception that indicates the threshold needs to be adjusted (too much of the path is being masked out)
            if(len(selected_pixels) < 10):
                raise Exception(f"Poor quality path{i+1}-{j+1}")

            # Calculate the amplitude of the heatmap from the path
            for x, y in selected_pixels: # Iterate through pixels on the path
                CMatrix[y][x][j] = 255 # This is a pixel on the path, set the Cmatrix value to 255
                for dy in range(int(-groupWidthWalking/2), int(1 + groupWidthWalking/2)): # Iterate through Y-pixels in the group around the path
                    for dx in range(int(-groupWidthWalking/2), int(1 + groupWidthWalking/2)): # Iterate through X-pixels in the group around the path
                        nx, ny = x + dx, y + dy # New pixel coordinates in the group around the path
                        distance = math.sqrt(dx**2 + dy**2) # Distance from the original pixel on the path
                        gaussianValue = (Rpath / (c * math.sqrt(2 * math.pi))) * math.exp(-((distance - b)**2) / (2 * c**2)) # Calculate the amplitude of the heatmap at the pixel
                        AMatrix[ny][nx][j] += gaussianValue # Increment the amplitude of the heatmap

            # Calculate the amplitude of the heatmap from the stops
            for stop in pathStops: # Iterate through all stops                 
                if(int(stop[4]) == j+1): # If the stop is on the current map
                    x, y = int(stop[2]), int(stop[3]) # Get the coordinates of the stop
                    t = stop[0] # Get the time spent at the stop
                    if(new_R_data[x, y] > 250): # If the pixel is white (i.e. is in a stairwell, shop, etc.)
                        xCorner = 0
                        yCorner = 0
                        # Find the bottom right corner
                        for dy in range(0, 30):
                            if(new_R_data[x, y+dy] < 100):
                                yCorner = y+dy
                        for dx in range(0, 30):
                            if(new_R_data[x+dx, y] < 100):
                                xCorner = x+dx
                        # Subtract the amplitude of the heatmap from the BMatrix in a 30 x 30 square (the pixel dimensions of the stairwells, shops, cafes, etc.)
                        for dy in range(-30, 0):
                            for dx in range(-30, 0):
                                BMatrix[yCorner + dy][xCorner + dx][j] -= RPerSec * t
                    else: # If the pixel is black (i.e. is within a room)
                        
                        # Same implementation as the path, but with a different, larger group width
                        for dy in range(int(-groupWidthStopping/2), int(1 + groupWidthStopping/2)):
                            for dx in range(int(-groupWidthStopping/2), int(1 + groupWidthStopping/2)):
                                nx, ny = x + dx, y + dy
                                distance = math.sqrt(dx**2 + dy**2)
                                gaussianValue = ((RPerSec * (t)) / (c * math.sqrt(2 * math.pi))) * math.exp(-((distance - b)**2) / (2 * c**2))
                                AMatrix[ny][nx][j] += gaussianValue

        except FileNotFoundError:
            print(f"File path{i+1}-{j+1}.png not found")
            pass

    i+=1 # Increment the path index

# Apply the heatmap to the red band of the map
for j in range(3): # Iterate through all maps
    map = Image.open(f"British_Museum_map_room_numbers-{j+1}.png") # Source a map with icons
    mapSource = map.split()
    R, G, B, A = 0, 1, 2, 3

    # Make the map black and white
    mapMask = mapSource[R].point(lambda i: i < 240 and 255) # any pixel greater than 240 is white, all others are black
    out1 = mapSource[R].point(lambda i: 0) # Set pixels to 0
    out2 = mapSource[G].point(lambda i: 0)
    out3 = mapSource[B].point(lambda i: 0)
    mapSource[R].paste(out1, None, mapMask) # Paste the black pixels onto the map
    mapSource[G].paste(out2, None, mapMask)
    mapSource[B].paste(out3, None, mapMask)
    blackmaps.append(mapSource)

    # Save the black maps for later use
    for idx, blackmap in enumerate(blackmaps):
        black_image = Image.merge(map.mode, blackmap)
        black_image.save(f"blackmap-{idx+1}.png")
        print(f"Successfully created blackmap-{idx+1}.png")

    # Create new bands
    new_R = mapSource[R].copy()
    new_G = mapSource[G].copy()
    new_B = mapSource[B].copy()
    new_R_data = new_R.load()
    new_G_data = new_G.load()
    new_B_data = new_B.load()
    
    # Apply the heatmap amplitudes in the A and B matricies to the red band of the map
    for y in range(map.size[1]): # Iterate through all Y-pixels in the map
        for x in range(map.size[0]): # Iterate through all X-pixels in the map
            if new_R_data[x, y] < 10: # If the pixel is black (i.e. is within a room / not a stairwell, shop, etc.)
                new_R_data[x, y] = int(min(255, AMatrix[y][x][j])) # Set the pixel value to the amplitude of the heatmap or to 255 if the amplitude is greater than 255
            elif new_R_data[x, y] > 240: # If the pixel is white (i.e. is within a room / not a stairwell, shop, etc.)
                new_G_data[x, y] = int(max(0, BMatrix[y][x][j]))
                new_B_data[x, y] = int(max(0, BMatrix[y][x][j]))
            
            # Displays paths on heatmap
            #if(CMatrix[y][x][j] > 0): # If the pixel is on the path
                #new_R_data[x, y] = 0
                #new_G_data[x, y] = 255
                #new_B_data[x, y] = 0

    # Combine the modified bands into a new image, crop and save it
    heatMap = Image.merge(map.mode, (new_R, new_G, new_B, mapSource[A]))
    heatmaps.append(heatMap)
    heatMap.crop((575, 75, 1750, 1800)).save(f"heatmap-{j+1}.png")
    print(f"Successfully created heatmap-{j+1}.png")

# filtered_artifacts contains all of the artifacts that were stopped at, filtering out artifacts the Unified Artifact Index that were not stopped at
# filtered_artifacts_eng contains all of the artifacts that were stopped at and have an engagement tag
# filtered_artifacts_vi contains all of the artifacts that were stopped at and have a visitor impact tag
filtered_artifacts = []
filtered_artifacts_eng = []
filtered_artifacts_vi = []
for artifact in allArtifacts: # Iterate through all artifacts
    if artifact[4] != 0: # if visits is not 0
        artifact[5] = round(artifact[5] / artifact[4]) # Calculate the average dwell time and round to the nearest unit digit

        # Calculate the average position of the artifact by averaging the positions of all stops associated with the artifact
        xsum = 0
        ysum = 0
        for pos in artifact[8]: # Iterate through the list of positions
            xsum += int(pos[0])
            ysum += int(pos[1])
        avgx = xsum / len(artifact[8])
        avgy = ysum / len(artifact[8])
        artifact[8] = ([round(avgx), round(avgy)])  # set the position for the artifact to the average position
        filtered_artifacts.append(artifact) # Add the artifact to the list of filtered artifacts
        if(artifact[6].get('eng', 0) + artifact[6].get('deng', 0) > 0): filtered_artifacts_eng.append(artifact) # If the artifact has an engagement tag, add it to the associated list
        if(artifact[6].get('b', 0) + artifact[6].get('st', 0) + artifact[6].get('dt', 0) > 0): filtered_artifacts_vi.append(artifact) # If the artifact has a visitor impact tag, add it to associated list

# Create a list of the popular artifacts
popular_artifacts = []
for artifact in filtered_artifacts: # Iterate through the filtered artifacts
    if artifact[4] > 4: # Define the threshold for a popular artifact
        popular_artifacts.append(artifact) # Add the artifact to the list of popular artifacts

# Write the list of filtered artifacts to a new csv file "Stopped Artifacts.csv"
with open('Stopped Artifacts.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(["Universal ID", "Audio Tour ID", "Name", "Room", "Visits", "Average Time", "Tags", "Comments", "Average Position", "Floor"])
    for artifact in filtered_artifacts:
        writer.writerow(artifact)
print(f"Successfully created Stopped Artifacts.csv")

# Write the list of popular artifacts to a new csv file "Popular Artifacts.csv"
with open('Popular Artifacts.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(["Universal ID", "Audio Tour ID", "Name", "Room", "Visits", "Average Time", "Tags", "Comments", "Average Position", "Floor"])
    for artifact in popular_artifacts:
        writer.writerow(artifact)
print(f"Successfully created Popular Artifacts.csv")

# Generates the popular artifacts map, displaying all of the popular artifacts as green dots on the map
i = 1 # Initialize the map index
for mapSource in blackmaps: # Source a blackmap 

    # Create new bands
    new_R = mapSource[R].copy()
    new_G = mapSource[G].copy()
    new_B = mapSource[B].copy()
    new_R_data = new_R.load()
    new_G_data = new_G.load()
    new_B_data = new_B.load()
    for artifact in popular_artifacts: # Iterate through the popular artifacts
        if(int(artifact[9]) == i): # if the artifact is on the current map
            pos = artifact[8] # Get the position of the artifact

            # Sets the pixel size of the dot on the map (11 x 11)
            for dy in range(-5, 5):
                for dx in range(-5, 5):
                    x = pos[0] + dx # update x
                    y = pos[1] + dy # update y

                    # Sets the color of the dot on the map, green
                    new_R_data[x, y] = 0
                    new_G_data[x, y] = 255
                    new_B_data[x, y] = 0

    popMap = Image.merge(map.mode, (new_R, new_G, new_B, mapSource[A]))

    # Draw the associated ID numbers onto the map
    draw = ImageDraw.Draw(popMap)
    fontsize = 15 # Sets the size of the ID number 
    font = ImageFont.truetype("arial.ttf", fontsize)
    for artifact in popular_artifacts: # Iterate through the popular artifacts again
        if(int(artifact[9]) == i): # if the artifact is on the current map
            pos = artifact[8] # get the position of the artifact
            pos = [pos[0] - 15, pos[1] - 25] # position the text relative to the dot (15 left and 25 up)

            # draw the ID number (text position, the ID number of the artifact, the color of the text, stroke width, and the font modified with the font size)
            draw.text(pos, str(artifact[0]), fill = (0, 255, 0), stroke_width = 0.2, font = font)

    # Crop and save the modified map
    popMap.crop((575, 75, 1750, 1800)).save(f"popmap-{i}.png")
    print(f"Successfully created popmap-{i}.png")
    i += 1

# Generates the stopped artifacts map, displaying all of the stopped artifacts as green dots on the map
# Method is the same as the popular artifacts, but the dots and text are smaller
i = 1
for mapSource in blackmaps:
    new_R = mapSource[R].copy()
    new_G = mapSource[G].copy()
    new_B = mapSource[B].copy()
    new_R_data = new_R.load()
    new_G_data = new_G.load()
    new_B_data = new_B.load()
    for artifact in filtered_artifacts:
        if(int(artifact[9]) == i):
            pos = artifact[8]
            for dy in range(-3, 3):
                for dx in range(-3, 3):
                    x = pos[0] + dx
                    y = pos[1] + dy
                    new_R_data[x, y] = 0
                    new_G_data[x, y] = 255
                    new_B_data[x, y] = 0
    # Save the modified heatmap
    stoppedMap = Image.merge(map.mode, (new_R, new_G, new_B, mapSource[A]))
    draw = ImageDraw.Draw(stoppedMap)
    fontsize = 10
    font = ImageFont.truetype("arial.ttf", fontsize)
    for artifact in filtered_artifacts:
        if(int(artifact[9]) == i):
            pos = artifact[8]
            pos = [pos[0] - 10, pos[1] - 15]
            draw.text(pos, str(artifact[0]), fill = (0, 255, 0), stroke_width = 0.2, font = font)

    stoppedMap.crop((575, 75, 1750, 1800)).save(f"stoppedmap-{i}.png")
    print(f"Successfully created stoppedmap-{i}.png")
    i += 1

# Generates an impact "heatmap", which was excluded from the final report due to the sparsity of data and an uncertainty in how to characterize the *amount* of impact.
# The current implementation uses both the frequency of the impact tags and the time spent at the artifact to determine the amplitude of the heatmap.
for i in range(3): # Iterate through the maps
    for artifact in filtered_artifacts_vi: # iterate through artifacts ITGs had visitor impact at
        if(int(artifact[9]) == i + 1): # if the artifact is on the current map
            # get the postion of the artifact
            pos = artifact[8] 
            x = int(pos[0])
            y = int(pos[1])

            # Get the number of tags for each type of visitor impact
            b_tags = artifact[6].get('b', 0)
            st_tags = artifact[6].get('st', 0)
            dt_tags = artifact[6].get('dt', 0)
            t = artifact[5] # Average time
            impact = (b_tags + st_tags + dt_tags) / artifact[4] # calculate impact (number of tags / number of visits)

            # Iterate through pixels around the artifact location
            for dy in range(int(-groupWidthStopping/2), int(1 + groupWidthStopping/2)):
                for dx in range(int(-groupWidthStopping/2), int(1 + groupWidthStopping/2)):
                    nx, ny = x + dx, y + dy # current pixel location
                    distance = math.sqrt(dx**2 + dy**2) # calculate distance from the current pixel to the artifact position
                    gaussianValue = ((RPerSec * t * impact) / (c * math.sqrt(2 * math.pi))) * math.exp(-((distance - b)**2) / (2 * c**2)) # caluclate the amplitude of the heatmap
                    DMatrix[ny][nx][i] += gaussianValue # increment the amplitude of the heatmap

# This applies the impact heatmap amplitude to the black maps
i = 0 # Initialize the map index
for mapSource in blackmaps: # Source a blackmap
    new_R = mapSource[R].copy()
    new_G = mapSource[G].copy()
    new_B = mapSource[B].copy()
    new_R_data = new_R.load()
    new_G_data = new_G.load()
    new_B_data = new_B.load()
    for y in range(map.size[1]): # Iterate through all Y-pixels in the map
        for x in range(map.size[0]): # Iterate through all X-pixels in the map
            if new_R_data[x, y] < 10: # If the pixel is black (i.e. is within a room / not a stairwell, shop, etc.)

                # Sets the color of the resulting heatmap (teal)
                new_G_data[x, y] = int(min(255, DMatrix[y][x][i])) # Set the pixel value to the amplitude of the heatmap
                new_B_data[x, y] = int(min(255, DMatrix[y][x][i])) # Set the pixel value to the amplitude of the heatmap

    # Crop and save the heatmaps
    impactMap = Image.merge(map.mode, (new_R, new_G, new_B, mapSource[A]))
    impactMap.crop((575, 75, 1750, 1800)).save(f"impactheatmap-{i+1}.png")
    print(f"Successfully created impactheatmap-{i+1}.png")
    i += 1

# Generates the engagmenet map, displaying all of the artifats with engagement as dots on the map with the color of the dot representing the engagement level.
i = 1 # map index
for mapSource in blackmaps: # iterate through blackmaps
    new_R = mapSource[R].copy()
    new_G = mapSource[G].copy()
    new_B = mapSource[B].copy()
    new_R_data = new_R.load()
    new_G_data = new_G.load()
    new_B_data = new_B.load()

    for artifact in filtered_artifacts_eng: # iterate through artifacts with engagement
        if(int(artifact[9]) == i): # if the artifact is on the current map
            pos = artifact[8] # get the position of the artifact

            # Get the relevant tags and calculate the engagment level
            eng_tags = artifact[6].get('eng', 0)
            deng_tags = artifact[6].get('deng', 0)
            engagement = (eng_tags - deng_tags) / artifact[4]

            # Set the pixel size of the dot on the map (11 x 11)
            for dy in range(-5, 5):
                for dx in range(-5, 5):
                    x = pos[0] + dx # update x
                    y = pos[1] + dy # update y

                    # Set the color of the dot on the map, yellow to purple, with yellow being the lowest engagement and purple being the highest
                    new_R_data[x, y] = 255
                    new_G_data[x, y] = 255 - round(255 * engagement)
                    new_B_data[x, y] = round(255 * engagement)
    engMap = Image.merge(map.mode, (new_R, new_G, new_B, mapSource[A]))

    # Draw the associated ID numbers onto the map (same as popular artifacts)
    draw = ImageDraw.Draw(engMap)
    fontsize = 15
    font = ImageFont.truetype("arial.ttf", fontsize)
    for artifact in filtered_artifacts_eng:
        if(int(artifact[9]) == i):
            pos = artifact[8]
            pos = [pos[0] - 15, pos[1] - 25]
            draw.text(pos, str(artifact[0]), fill = (0, 255, 255), stroke_width = 0.2, font = font)

    # Crop and save the modified heatmap
    engMap.crop((575, 75, 1750, 1800)).save(f"engmap-{i}.png")
    print(f"Successfully created engmap-{i}.png")
    i += 1

# Generates the visitor impact map, displaying all of the artifacts with visitor impact as dots on the map with the color of the dot representing the frequency of ITG impact.
# Method is the same as the engagement map, but the dots are green and red, with green representing a low frequency of impact and red representing a high frequency of impact.
i = 1 
for mapSource in blackmaps: #
    new_R = mapSource[R].copy()
    new_G = mapSource[G].copy()
    new_B = mapSource[B].copy()
    new_R_data = new_R.load()
    new_G_data = new_G.load()
    new_B_data = new_B.load()

    for artifact in filtered_artifacts_vi: 
        if(int(artifact[9]) == i): 
            pos = artifact[8] 
            tags = artifact[6].get('st', 0) + artifact[6].get('b', 0) + artifact[6].get('dt', 0) # get the number of visitor impact tags
            normalizedTags = (tags) / artifact[4] # normalize the number of tags by dividing by the number of visits
            for dy in range(-5, 5):
                for dx in range(-5, 5):
                    x = pos[0] + dx
                    y = pos[1] + dy
                    # Color scale: green to red, with green being the lowest frequency of impact and red being the highest
                    new_R_data[x, y] = round(255 * normalizedTags)
                    new_G_data[x, y] = 255 - round(255 * normalizedTags)
                    new_B_data[x, y] = 0
    viMap = Image.merge(map.mode, (new_R, new_G, new_B, mapSource[A]))
    draw = ImageDraw.Draw(viMap)
    fontsize = 15
    font = ImageFont.truetype("arial.ttf", fontsize)
    for artifact in filtered_artifacts_vi:
        if(int(artifact[9]) == i):
            pos = artifact[8]
            pos = [pos[0] - 15, pos[1] - 25]
            draw.text(pos, str(artifact[0]), fill = (0, 255, 255), stroke_width = 0.2, font = font)
    viMap.crop((575, 75, 1750, 1800)).save(f"impactmap-{i}.png")
    print(f"Successfully created impactmap-{i}.png")
    i += 1


# Write the updated artifact index to a new csv file excluding certain columns and breaking out tags for easier analysis
with open('Filtered Stopped Artifacts.csv', 'w', newline='', encoding='utf-8-sig') as f: # open or create the associated csv file
    writer = csv.writer(f)
    writer.writerow(["Universal ID", "Name", "Visits", "Average Time", "SP", "ENG", "DENG", "B", "ST", "DT", "FA", "BG"]) # define the columns
    for artifact in filtered_artifacts:
        tags = artifact[6] # get the tags
        writer.writerow([ # write the rows
            artifact[0], artifact[2], artifact[4], artifact[5],
            tags.get('sp', 0), tags.get('eng', 0), tags.get('deng', 0),
            tags.get('b', 0), tags.get('st', 0), tags.get('dt', 0),
            tags.get('fa', 0), tags.get('bg', 0)
        ])
print(f"Successfully created Filtered Stopped Artifacts.csv")

# Do the same for popular artifacts
with open('Filtered Popular Artifacts.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(["Universal ID", "Name", "Visits", "Average Time", "SP", "ENG", "DENG", "B", "ST", "DT", "FA", "BG"])
    for artifact in popular_artifacts:
        tags = artifact[6]
        writer.writerow([
            artifact[0], artifact[2], artifact[4], artifact[5],
            tags.get('sp', 0), tags.get('eng', 0), tags.get('deng', 0),
            tags.get('b', 0), tags.get('st', 0), tags.get('dt', 0),
            tags.get('fa', 0), tags.get('bg', 0)
        ])
print(f"Successfully created Filtered Popular Artifacts.csv")