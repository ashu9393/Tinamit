import os

soil_class = {
    # Jhang
    '1': [
        # [0.45, 0.53],
        # [0.45, 0.49],
        # [0.45, 0.9],
        [26, 158],
        [26, 158],
        # [26, 158],
        # [26, 158],
        # [0.65, 0.75],
        # [0.65, 0.75],
        # [0.65, 0.75],
        [0.31, 0.42],
        # [0.31, 0.38],
        [0.31, 0.5]
        ],
    # Farida
    '2': [
        # [0.44, 0.50],
        # [0.44, 0.46],
        # [0.44, 0.9],
        [26, 120],
        [26, 120],
        # [26, 120],
        # [26, 120],
        # [0.65, 0.75],
        # [0.65, 0.75],
        # [0.65, 0.75],
        [0.36, 0.43],
        # [0.36, 0.38],
        [0.36, 0.5]
        ],
    # Chuharkana
    '3': [
        # [0.45, 0.55],
        # [0.45, 0.47],
        # [0.43, 0.9],
        [26, 103],
        [26, 103],
        # [26, 103],
        # [26, 103],
        # [0.65, 0.75],
        # [0.65, 0.75],
        # [0.65, 0.75],
        [0.4, 0.46],
        # [0.4, 0.42],
        [0.4, 0.5]
        ],

    # Chuharkana
    '4': [
        # [0.43, 0.55],
        # [0.42, 0.52],
        # [0.42, 0.9],
        [26, 52],
        [26, 52],
        # [26, 52],
        # [26, 52],
        # [0.65, 0.75],
        # [0.65, 0.75],
        # [0.65, 0.75],
        [0.08, 0.35],
        # [0.25, 0.3],
        [0.25, 0.5]
        ]
}

# print(soil_class[str(1)])

p_soil_class = [1,
                1,
                2,
                2,
                3,
                2,
                2,
                2,
                3,
                2,
                3,
                3,
                2,
                2,
                3,
                3,
                1,
                2,
                3,
                2,
                2,
                3,
                1,
                1,
                2,
                2,
                1,
                3,
                1,
                2,
                2,
                3,
                3,
                3,
                3,
                1,
                1,
                2,
                2,
                3,
                3,
                2,
                2,
                1,
                2,
                3,
                3,
                1,
                2,
                3,
                2,
                1,
                2,
                2,
                3,
                3,
                2,
                2,
                3,
                3,
                2,
                2,
                2,
                2,
                2,
                1,
                2,
                3,
                2,
                3,
                3,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                3,
                3,
                3,
                3,
                2,
                1,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                3,
                1,
                3,
                3,
                3,
                1,
                1,
                1,
                2,
                2,
                2,
                2,
                2,
                2,
                1,
                1,
                1,
                3,
                3,
                3,
                2,
                1,
                2,
                1,
                1,
                3,
                3,
                3,
                2,
                2,
                1,
                1,
                3,
                1,
                1,
                2,
                2,
                2,
                1,
                1,
                2,
                1,
                1,
                1,
                1,
                1,
                3,
                3,
                4,
                4,
                4,
                2,
                2,
                2,
                4,
                2,
                2,
                1,
                2,
                2,
                2,
                2,
                3,
                4,
                4,
                4,
                4,
                4,
                4,
                4,
                4,
                4,
                2,
                2,
                2,
                1,
                2,
                2,
                2,
                2,
                2,
                4,
                4,
                2,
                2,
                4,
                4,
                4,
                4,
                1,
                1,
                1,
                1,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                4,
                2,
                2,
                2,
                1,
                1,
                1,
                1,
                2,
                4,
                4,
                2,
                1,
                1,
                1,
                1,
                1,
                2,
                2,
                1,
                1,
                1]
