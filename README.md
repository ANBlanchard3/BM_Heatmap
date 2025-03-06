<a id="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ANBlanchard3/BM_Heatmap">
    <img src="Project Picture.jpg" alt="Logo" width="540" height="469">
  </a>
<br />
<br />
<h1 align="center">International Tour Groups at the British Museum</h1>

  <p align="center">
    The project represents the work of undergraduate students at Worcester Polytechnic Institute on behalf of the British Museum. The British Museum, located in Bloomsbury, London, attracts millions of international visitors, many of which experience the Museum through private tours. Despite the prevalence of these international tour groups, their behaviours, impacts, and needs were not fully understood. This study developed methods for recording and visualizing group behaviours and impacts across the Museum. Sixteen ITGs were observed to construct a typical visit, and five ITG guides were interviewed to understand their experiences. Observations revealed that ITGs visit similar items, take similar paths, and impact other visitors. From these findings, the authors recommended specific changes to the Museum’s group visitation guidelines and the design of galleries to improve the experience of all visitors. For details, see the full report and published project below:
    <br />
    <br />
    <a href="https://wp.wpi.edu/london/projects/2025-projects-winter/british-museum/"><strong>Read our Full Report »</strong></a>
    <br />
    <br />
    <a href="https://github.com/ANBlanchard3/BM_Heatmap"><strong>Explore the docs »</strong></a>
    <br />
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project
This project is the impementation of a method for organizing and visualizing observation data on specific groups accross a museum. Included is the data from observing 16 international tour groups at the British Museum and the generated visuals. These visuals include a heatmap showing where the groups spend the most time, and maps with dots showing the frequency of various behaviors of interest at specific locations. 

Some effort has been made to ensure this implementation is relatively flexible, and can be adapted to observing groups and their behaviors throughout any space that can be mapped.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

If you aren't familiar with Python, this section will get you started.

1. Set up a python editor and interpreter. I recommend following the [quick start guide](https://code.visualstudio.com/docs/python/python-quick-start) for VS Code.
2. From here you can download the project from this github page, unzip it, and open it in VS Code. Alternatively, if you intend to make significant changes or additions to the script, you can [set up Git in VS Code](https://code.visualstudio.com/docs/sourcecontrol/intro-to-git) and clone the repository.

### Prerequisites

Before you run the code, you'll have to download the Python Imaging Library by entering the following lines using command prompt:

  ```sh
  python3 -m pip install --upgrade pip
  python3 -m pip install --upgrade Pillow
  ```

The code should now run. If you are having issues with packages, refer to the [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/installing-packages/) or the [Basic Installation Page](https://pillow.readthedocs.io/en/latest/installation/basic-installation.html) for the Python Imaging Library.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage
The script itself is the `HeatmapGenerator.py` file. Running it will generate a series of output files 
Included in the project files are files that are necessary for the code to run, files containing data, and files that are output.

#### Required Files
The files that are required for the code to run are the maps:
`British_Museum_map_no_icons-1.png` 
`British_Museum_map_no_icons-2.png`
`British_Museum_map_no_icons-3.png`

and

`British_Museum_map_room_numbers-1.png`
`British_Museum_map_room_numbers-2.png`
`British_Museum_map_room_numbers-3.png`

The code is fundamentally structured for multiple maps, but can easily be modified for more or fewer maps (including 1 map). The maps without icons are used to roughly display a heatmap within the stairwell or restroom icons on the British Museum map. This particular implementation assumes that stops located on non white parts of the map are normal stops, and stops on white parts of the map are icon stops. The naming structure ending in the `-i` where i is the map number is important for the function of the code.

The other required file is the `Unified Artifact Index.csv`. The artifacts in this file have unique audio tour IDs that were convenient for consistently and quickly noting down stop locations during observation. All artifacts that are referred to by this audio tour ID must be in this list. Artifacts in the list that are not visited will be filtered out. Artifacts that are referred to by a number and are not in this list are ignored and a warning is printed.

#### Data Files
All files containing data start with path. Each observed group has 1 .csv file, and a .png file for each map the group travelled on.
 Every observed group in the included data travelled on two maps, with only group 16 travelling on the third map. Thus, all of the data for group 16 is in the files:
 `path16.csv`
  `path16-1.png`
  `path16-2.png`
  `path16-3.png`

Once again, the numbering `pathk-i ` format is important, where k is the group number (starting at 1) and i is the established map number.

#### Output files
Output files include:

`engmap-i.png` (maps of engagement at artifacts across the Museum)

`heatmap-i.png` (heatmaps)

`impactheatmap-i.png` (maps of ITG visitor impact at artifacts across the Museum)

`impactmap-i.png` (heatmaps of this ITG visitor impact)

`popmap-i.png` (maps of the most popular artifacts)

`Popular Artifacts.csv` (list of the most popular artifacts containing data by artifact)

`Stopped Artifacts.csv` (list of all of the visited artifacts containing data by artifact)

`stoppedmap-i.png` (maps of all of the visited artifacts)

These files can be safely deleted and will be re-generated or updated every time the script is run.

### Data Organization and Generation
To begin with the path .csv files. For the duration of the project these files were kept as Excel files and converted to a CSV UTF-8 format for easy processing. Some understanding of the way the script parses stops from this file is useful when transcribing data. Starting from the first lap, the script will first look at the `X Location` column, looking for the first stop. Once a lap is reached with a location, it will look at the `Travel/Dwell` column for future laps until a `T`. Thus, a `D` in the following row indicates the group is continuing to dwell in the same location at the same artifact, and a `T` indicates the group has started moving again and the script can begin looking for the next stop. The only other consideration is when recording stops without a location. This was done when the group disperses. In these cases, it is important a `T` is recorded in the row prior to the dispersion. If the group was dwelling at an object, and then dispersed without travelling, there should be a 0 second lap prior to the dispersion lap. This should be set to a `T`. For more details on how the raw data was gathered during observations, refer to the Methods chapter of our report.

Other considerations are:
* the time in the `Dwell/Travel Time` column can be in h:mm:ss or mm:ss format. 
* Object names must be consistent from path to path
* Object names or portions of names in parentheses are ignored. Stops that did not take place at particular artifacts should be put in parentheses.
* The X and Y Locations correspond to the X, Y pixel coordinate of the approximate location the group stopped on the museum map.
* The `floor` column refers to the map the stop was on, not the actual floor / level of the Museum.
* The tags should be listed with a single space between them.

A good example for a long and relatively complex path can be found in `path9.csv`. This file can be opened in Excel for easy viewing.

To generate the path .pngs, Inkscape was used. The museum map was opened ensuring it opened in its default size. Then, a spline path was drawn onto the map digitizing the path drawn during observation. This once complete, this path was then isolated from the map and saved as a .png, once again ensuring the size of the resulting .png matched the original map. The parameters used when drawing the path were drawn with HSL values of 120, 100, 50 with opacity set to 50% and a 0.915 pixel width.

In order to add more groups to the dataset, simply add more path .csv and .png files following the established naming convention. The script will iterate through .csv files until the next cannot be found. Then, it will iterate through the .png files for that group in the same way.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Email: anblanchard3@gmail.com

Project Link: [https://github.com/ANBlanchard3/BM_Heatmap](https://github.com/ANBlanchard3/BM_Heatmap)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/ANBlanchard3/BM_Heatmap.svg?style=for-the-badge
[contributors-url]: https://github.com/ANBlanchard3/BM_Heatmap/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/ANBlanchard3/BM_Heatmap.svg?style=for-the-badge
[forks-url]: https://github.com/ANBlanchard3/BM_Heatmap/network/members
[stars-shield]: https://img.shields.io/github/stars/ANBlanchard3/BM_Heatmap.svg?style=for-the-badge
[stars-url]: https://github.com/ANBlanchard3/BM_Heatmap/stargazers
[issues-shield]: https://img.shields.io/github/issues/ANBlanchard3/BM_Heatmap.svg?style=for-the-badge
[issues-url]: https://github.com/ANBlanchard3/BM_Heatmap/issues
[license-shield]: https://img.shields.io/github/license/ANBlanchard3/BM_Heatmap.svg?style=for-the-badge
[license-url]: https://github.com/ANBlanchard3/BM_Heatmap/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 