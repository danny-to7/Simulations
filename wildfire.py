import numpy as np
import math
import matplotlib.pyplot as plt
import scipy.spatial.distance as distance
from matplotlib import animation
from matplotlib import colors
import time

# Displacements from a cell to its eight nearest neighbours
neighbourhood = ((-1,-1), (-1,0), (-1,1), (0,-1), (0, 1), (1,-1), (1,0), (1,1))
BURNING1, BURNING2, BURNING3, BURNING4, BURNT = 0, 1, 2, 3, 4
GRASS, BRUSH, TREE, WATER, EMPTY = 5, 6, 7, 8, 9

fuel_loads = {GRASS:5, BRUSH:7, TREE:20, WATER:1}

colors_list = ['darkorange', 'orangered', 'firebrick', 'darkred', (0.2,0,0),
'forestgreen', 'darkolivegreen', 'darkgreen', 'navy', 'goldenrod', 'sienna']
cmap = colors.ListedColormap(colors_list)
bounds = [0,1,2,3,4,5,6,7,8,9,10]
norm = colors.BoundaryNorm(bounds, cmap.N)

fig = plt.figure(figsize=(37.5/3, 9.375))#(figsize=(25/3, 6.25))
ax = fig.add_subplot(111)
ax.set_axis_off()
# im = ax.imshow(np.zeros((0,0)), cmap=cmap, norm=norm)#, interpolation='nearest')

class FireSim:

    def __init__(self, nx, ny):
        # Forest size (number of cells in x and y directions).
        self.nx, self.ny = nx, ny
        self.X = [[None for y in range(ny)] for x in range(nx)]
        self.cell_states = np.full((ny, nx), EMPTY)
        self.wind = [15, 45]
        # self.populate_cells()
        self.get_cells()
        self.copy_X = self.X
        self.burning_cells = []
        self.ignite_location()
        # self.update_states()

    def iterate(self):
        self.delete_burnt()
        new_burning_cells = []

        for i in range(0, len(self.burning_cells)):
            x = self.burning_cells[i].x
            y = self.burning_cells[i].y
            state = self.burning_cells[i].get_state()
            # intensity = self.burning_cells[i].fire_intensity

            for dx, dy in neighbourhood:
                if self.X[y+dy][x+dx] == None or self.X[y+dy][x+dx].get_state() in (WATER, BURNT):
                    continue

                neighbour_state = self.X[y+dy][x+dx].get_state()

                if neighbour_state > BURNT:
                    fire_chance = np.random.uniform()
                    ignition_prob =  self.burning_cells[i].get_prob(neighbour_state)
                    if ignition_prob >= fire_chance:
                        self.X[y+dy][x+dx].burn()
                        new_burning_cells.append(self.X[y+dy][x+dx])
                # if self.X[y+dy][x+dx].get_state() > BURNT:
                #     fire_chance = np.random.uniform()
                #     if self.X[y+dy][x+dx].ignition_prob >= fire_chance:
                #         self.X[y+dy][x+dx].set_state(0)
                #         self.burning_cells.append(self.X[y+dy][x+dx])


            self.burning_cells[i].burn()
        self.burning_cells =  self.burning_cells + new_burning_cells
            # if state < 4:
            #     self.burning_cells[i].set_state(state+1)

    def animate(self, i):
        self.update_states()
        im.set_data(self.cell_states)
        self.iterate()

    def get_cells(self):
        gen = WorldGen(self.nx, self.ny)
        self.cell_states = gen.generate_cells(9)
        print self.cell_states
        for ix in range(1, self.nx-1):
            for iy in range(1, self.ny-1):
                cell_type = self.cell_states[iy,ix]
                self.X[iy][ix] = Cell(cell_type, ix, iy)

    def populate_cells(self):
        cell_types = [GRASS, BRUSH, TREE]

        for ix in range(1,self.nx-1):
            for iy in range(1,self.ny-1):
                temp = cell_types[np.random.randint(0, len(cell_types))]
                self.X[iy][ix] = Cell(temp, ix, iy)
                self.cell_states[iy, ix] = temp

    def update_states(self):
        for ix in range(1,self.nx-1):
            for iy in range(1,self.ny-1):
                self.cell_states[iy, ix] = self.X[iy][ix].get_state()

    def ignite_location(self):
        x = np.random.randint(1, self.nx-1)
        y = np.random.randint(1, self.ny-1)
        self.X[y][x].burn()
        self.burning_cells.append(self.X[y][x])

    def delete_burnt(self):
        delete_cells = []

        for i in range(0, len(self.burning_cells)):
            if self.burning_cells[i].get_state() == 4:
                delete_cells.append(i)

        self.burning_cells = [v for i, v in enumerate(self.burning_cells) if i not in delete_cells]

class Cell:

    def __init__(self, cell_type, x, y):
        self.state = cell_type
        self.x = x
        self.y = y
        self.fuel = fuel_loads[cell_type]
        self.burning_time = 0
        # self.ignition_prob = self.fire_intensity()
        self.recalculate_ignition_prob()

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def fire_intensity(self):
        return 1 - self.burnt_percent()

    def burnt_percent(self):
        return self.burning_time / float(self.fuel)

    def recalculate_ignition_prob(self):
        if self.state == GRASS:
            self.ignition_prob = {GRASS: 0.25, TREE: 0.075, BRUSH: 0.15}
            # self.ignition_prob = 0.175 * self.fire_intensity()

        elif self.state == TREE:
            self.ignition_prob = {GRASS: 0.225, TREE: 0.05, BRUSH: 0.125}
            # self.ignition_prob = 0.05 * self.fire_intensity()

        elif self.state == BRUSH:
            self.ignition_prob = {GRASS: 0.225, TREE: 0.125, BRUSH: 0.15}
            # self.ignition_prob = 0.125 * self.fire_intensity()

        pass

    def burn(self):
        self.burning_time += 1
        self.state = int(self.burnt_percent() * 100 / 25)

    def get_prob(self, state):
        return self.ignition_prob[state] * self.fire_intensity()

class WorldGen:

    def __init__(self, nx, ny):
        self.tree_density = 0.525
        self.brush_density = 0.425
        self.nx, self.ny = nx, ny
        self.X = np.full((ny, nx), EMPTY)
        self.water_bodies = 3
        self.water_size = 3000
        self.area_variance = 0.5
        # self.X = [[None for y in range(ny)] for x in range(nx)]

    def generate_first(self):
        tree_density = self.tree_density
        brush_density = self.brush_density
        for ix in range(1,self.nx-1):
            for iy in range(1,self.ny-1):
                temp = np.random.uniform()
                if temp <= tree_density:
                    self.X[iy,ix] = TREE

                elif temp <= brush_density+tree_density:
                    self.X[iy,ix] = BRUSH

                else:
                    self.X[iy,ix] = GRASS

    def generate_rest(self, iterations):
        min_neighbours = 4

        for i in range(0, iterations):
            for ix in range(1,self.nx-1):
                for iy in range(1,self.ny-1):
                    if self.X[iy,ix] == WATER:
                        continue

                    tree_neighbours = 0
                    brush_neighbours = 0
                    for dx, dy in neighbourhood:
                        if self.X[iy+dy, ix+dx] == GRASS:
                            continue

                        if self.X[iy+dy, ix+dx] == TREE:
                            tree_neighbours += 1

                        elif self.X[iy+dy, ix+dx] == BRUSH:
                            brush_neighbours += 1

                    if self.X[iy,ix] == TREE and tree_neighbours >= min_neighbours:
                        self.X[iy,ix] = TREE

                    elif self.X[iy,ix] != TREE and tree_neighbours >= min_neighbours+1:
                        self.X[iy,ix] = TREE

                    elif self.X[iy,ix] == BRUSH and brush_neighbours >= min_neighbours:
                        self.X[iy,ix] = BRUSH

                    elif self.X[iy,ix] != BRUSH and brush_neighbours >= min_neighbours+1:
                        self.X[iy,ix] = BRUSH

                    else:
                        self.X[iy,ix] = GRASS

    def generate_water(self):
        bodies = self.water_bodies
        area = self.water_size
        density = 0.6
        radius = int(math.sqrt(area/math.pi))

        points = self.generate_centres()
        # np.random.seed(int(time.time()))
        #
        # for i in range(0, bodies):
        #     x = np.random.randint(1+radius, self.nx-1-radius)
        #     y = np.random.randint(1+radius, self.ny-1-radius)
        #     points.append([x,y])

        print points
        for i in points:
            self.fill_water(i)
            # for x in range(0, area):
            #     temp = np.random.uniform()
            #     if temp <= density:
            #         temp_x = np.random.randint(i[0]-radius, i[0]+radius)
            #         temp_y = np.random.randint(i[1]-radius, i[1]+radius)
            #         self.X[temp_y,temp_x] = WATER
            # for ix in range(i[0]-area,i[0]+area):
            #     for iy in range(i[1]-area,i[1]+area):
            #         temp = np.random.uniform()
            #         if temp <= density:
            #             self.X[iy,ix] = WATER

        min_neighbours = 4

        for i in range(0, 4):
            for ix in range(1,self.nx-1):
                for iy in range(1,self.ny-1):
                    neighbours = 0
                    for dx, dy in neighbourhood:
                        if self.X[iy+dy, ix+dx] == WATER:
                            neighbours += 1

                    if self.X[iy,ix] == WATER and neighbours >= min_neighbours:
                        self.X[iy,ix] = WATER

                    elif self.X[iy,ix] != WATER and neighbours >= min_neighbours+1:
                        self.X[iy,ix] = WATER

                    # else:
                    #     self.X[iy,ix] = GRASS

    def generate_centres(self):
        points = []
        area = self.water_size

        np.random.seed(int(time.time()))
        radius = int(math.sqrt(area/math.pi))

        for i in range(0, self.water_bodies):
            x = np.random.randint(1+radius, self.nx-1-radius)
            y = np.random.randint(1+radius, self.ny-1-radius)

            while self.check_against_points([x,y], points) == False:
                x = np.random.randint(1+radius, self.nx-1-radius)
                y = np.random.randint(1+radius, self.ny-1-radius)

            points.append([x,y])

        return points

    def check_against_points(self, point, points):
        area = self.water_size
        radius = int(math.sqrt(area/math.pi))
        for i in points:
            dist = int(distance.euclidean(point, i))
            # print dist < radius
            if dist < radius:
                return False

        return True

    def fill_water(self, point):
        area = int(self.water_size * 0.45)
        print area
        radius = int(math.sqrt(self.water_size/math.pi))
        # print radius
        count = 0

        while count <= area:
            temp_x = np.random.randint(-radius, radius)
            temp_y = np.random.randint(-radius, radius)
            # print temp_x, temp_y
            if self.X[point[1]+temp_y, point[0]+temp_x] != WATER:
                # print True
                dist = int(math.sqrt((temp_y)**2 + (temp_x)**2))
                # print int(distance.euclidean(point, [temp_x, temp_y]))
                # if int(distance.euclidean(point, [temp_y, temp_x])) <= radius**2:
                if dist <= radius:
                    # print True
                    self.X[point[1]+temp_y, point[0]+temp_x] = WATER
                    count += 1
                    # print count

        # for i in range(0, area):
        #     temp_x = np.random.randint(-radius, radius)
        #     temp_y = np.random.randint(-radius, radius)
        #
        #     if self.X[point[1]+temp_y, point[0]+temp_x] != WATER:
        #         self.X[point[1]+temp_y, point[0]+temp_x] = WATER

    def generate_cells(self, iterations):
        self.generate_first()
        self.generate_rest(iterations)
        self.generate_water()
        return self.X


fire = FireSim(300, 300)
im = ax.imshow(fire.cell_states, cmap=cmap, norm=norm)
interval = 50
anim = animation.FuncAnimation(fig, fire.animate, interval=interval)
plt.show()
