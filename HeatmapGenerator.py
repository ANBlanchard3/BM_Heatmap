import sys
import math
from PIL import Image, ImageChops
import csv
import os.path

# Load the maps outside of the loop as they do not change
map1 = Image.open("British_Museum_map-1.png")
map2 = Image.open("British_Museum_map-2.png")
map3 = Image.open("British_Museum_map-3.png")

# Constants / Parameters
RPerSec = 10 #.1
pixelSize = 10 # pixels per meter
walkSpeed = .5 # meters per second
walkSpeed = walkSpeed * pixelSize # Pixels per second
groupWidthWalking = 15 # pixels
groupWidthStopping = 50 # pixels
Rpath = 100 #(1 / walkSpeed) * RPerSec * groupLength

# Gaussian Function Definition
a = 1 # Amplitude of the curve is 0-1
b = 0 # center the curve on 0
c = groupWidthWalking/3 # std deviation

i = 0 # path index

# Create a 3D matrix the size of the map to store the amplitude of the heatmap at each pixel for each map
# The AMatrix is added to the red band of black areas on the map to create the heatmap in rooms
# The BMatrix is subtracted from the green and blue bands of white areas on the map to create the heatmap in stairs, shops, cafes, etc.
AMatrix = [[[0] * 3 for _ in range(map1.size[0])] for _ in range(map1.size[1])]
BMatrix = [[[255] * 3 for _ in range(map1.size[0])] for _ in range(map1.size[1])]

# Iterate over every path file until no more exist
while os.path.exists(f"path{i+1}_1.png") or os.path.exists(f"path{i+1}_2.png") or os.path.exists(f"path{i+1}_3.png"):
    print(f"Generating path {i+1}")

    # Read path positions from csv files
    positions_list = []
    times_list = []
    for j in range(3):
        positions = []
        times = []
        try:
            with open(f"path{i+1}_{j+1}.csv", newline='', encoding='utf-8-sig') as f:
                print(f"Reading path{i+1}_{j+1}.csv")
                reader = csv.reader(f)
                path = list(reader)
                for row in path:
                    positions.append([int(row[0]), int(row[1])])
                    times.append(int(row[2]))
        except FileNotFoundError:
            print(f"File path{i+1}_{j+1}.csv not found")
            pass
        positions_list.append(positions)
        times_list.append(times)

    # Iterate over each map
    for j in range(3):
        times = times_list[j]
        positions = positions_list[j]
        try:
            path = Image.open(f"path{i+1}_{j+1}.png") # Load the path
            print(f"Reading path{i+1}_{j+1}.png")
            map = Image.open(f"British_Museum_map_no_icons-{j+1}.png") # Load the map
            pathSource = path.split()
            mapSource = map.split()

            # Create a mask for the path
            R, G, B, A = 0, 1, 2, 3

            new_R = mapSource[R].copy()
            new_R_data = new_R.load()

            mask = pathSource[A].point(lambda i: i > 126 and 255) # 126 oppacity mask to isolate a one pixel wide path independent of the width of the path drawn in Inkscape

            # Get the coordinates of the selected pixels in the mask
            selected_pixels = [(x, y) for y in range(mask.size[1]) for x in range(mask.size[0]) if mask.getpixel((x, y)) == 255]

            # Calculate the amplitude of the heatmap from the path
            for x, y in selected_pixels: # Iterate through pixels in the mask
                for dy in range(int(-groupWidthWalking/2), int(1 + groupWidthWalking/2)): # Iterate through Y-pixels in the group
                    for dx in range(int(-groupWidthWalking/2), int(1 + groupWidthWalking/2)): # Iterate through X-pixels in the group
                        nx, ny = x + dx, y + dy # New pixel coordinates
                        distance = math.sqrt(dx**2 + dy**2) # Distance from the original pixel on the path
                        gaussianValue = (Rpath / (c * math.sqrt(2 * math.pi))) * math.exp(-((distance - b)**2) / (2 * c**2))
                        AMatrix[ny][nx][j] += gaussianValue # Increment the amplitude of the heatmap

            # Calculate the amplitude of the heatmap from the stopping points
            t = 0 # Index for the time spent at each stopping point from the csv file
            for x, y in positions:
                if(new_R_data[x,y] > 250): # If the pixel is white (i.e. is not within a room / a stairwell, shop, etc.)
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
                            BMatrix[yCorner + dy][xCorner + dx][j] -= RPerSec * times[t]
                else: # If the pixel is black (i.e. is within a room)
                    for dy in range(int(-groupWidthStopping/2), int(1 + groupWidthStopping/2)):
                        for dx in range(int(-groupWidthStopping/2), int(1 + groupWidthStopping/2)):
                            nx, ny = x + dx, y + dy
                            distance = math.sqrt(dx**2 + dy**2)
                            gaussianValue = ((RPerSec * (times[t])) / (c * math.sqrt(2 * math.pi))) * math.exp(-((distance - b)**2) / (2 * c**2))
                            AMatrix[ny][nx][j] += gaussianValue
                t += 1 # Increment the time index

        except FileNotFoundError:
            print(f"File path{i+1}_{j+1}.png not found")
            pass

    i+=1 # Increment the path index

# Apply the heatmap to the red band of the map
for j in range(3): # Iterate through all maps
    map = Image.open(f"British_Museum_map-{j+1}.png") # Source a fresh map
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

    # Create new images for the modified bands
    new_R = mapSource[R].copy()
    new_G = mapSource[G].copy()
    new_B = mapSource[B].copy()
    new_R_data = new_R.load()
    new_G_data = new_G.load()
    new_B_data = new_B.load()
    
    for y in range(map.size[1]): # Iterate through all Y-pixels in the map
        for x in range(map.size[0]): # Iterate through all X-pixels in the map
            if new_R_data[x, y] < 10: # If the pixel is black (i.e. is within a room / not a stairwell, shop, etc.)
                new_R_data[x, y] = int(min(255, AMatrix[y][x][j])) # Set the pixel value to the amplitude of the heatmap or to 255 if the amplitude is greater than 255
            elif new_R_data[x, y] > 240: # If the pixel is white (i.e. is within a room / not a stairwell, shop, etc.)
                new_G_data[x, y] = int(max(0, BMatrix[y][x][j]))
                new_B_data[x, y] = int(max(0, BMatrix[y][x][j]))

    # Combine the modified bands into a new image
    heatMap = Image.merge(map.mode, (new_R, new_G, new_B, mapSource[A]))
    heatMap.save(f"heatmap_{j+1}.png")
    print(f"Successfully created heatmap_{j+1}.png")