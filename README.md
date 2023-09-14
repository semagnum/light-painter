![Light Painter](/assets/logo.png)

Welcome to the official Light Painter documentation!
Here you can learn how to use the Blender add-on and dive into the Python package.

## Painting

![List of tools: Light Paint, Mesh Light Paint, Tube Light Paint, Sky Paint, Shadow Paint](/docs/assets/tools.png)

The painting is done within each tool.
Once installed, you can find these tools on the left-hand side of the 3D view
in the toolshelf (`T` it the default shortcut to hide/reveal this shelf).
When the tool is selected, left-click the mouse to start the tool.

From there, you can use the mouse left-click and right-click
to draw and erase marks on surfaces respectively.
Press `Escape` key to cancel, and the `Return/Enter` key to add light.

Now just paint where you want the light to hit your objects' surfaces!

### What's the best way to paint?

![Adding a light, step by step](/docs/assets/painting_steps.gif)

You do not need to fill in every surface.
Draw some simple strokes over surfaces that you would like highlighted by your light.
Keep in mind that the surface's normal you are drawing over
can influence where the light will be finally positioned.

The tool also works best
when your strokes matches the shape of the type of lamp that you want.

Here are some general painting tips:

- Draw on multiple surfaces. The operators can handle most cases
  where surfaces face different directions,
  but it will fail if the average of the surface direction is zero.
- Spot lamps prefer circular strokes.
  But if you do not trust your drawing ability,
  a painted line representing the diameter is sufficient.
- Area lamps prefer rectangles, squares, circles or a single painted line.
- Point lamps are the most forgiving since a point lamp's rotation
  is irrelevant to its ability to light.

## Light Paint

You can choose between the main light types (for the sun lamp, see "Sky Paint"):

- point lamp
- spot lamp
- area lamp

Like with any of the tools, you can press `F9` or click the collapsed Redo Panel
in the bottom-left corner of the 3D view to tweak parameters, such as:
- Light color.
- Light distance and power. For lamp objects, a "Relative" toggle is available.
  When enabled, this allows you to adjust light coverage and falloff by adjust the lamp distance,
  without affecting apparent brightness.
- Ray visibility settings, to tweak light or object visibility 
  for diffuse, specular, or volumetric rays or shaders.
  Note that these ray visibility settings will be dependent on your render engine's implementation,
  as Eevee and Cycles handle visibility differently or may ignore it.

### Adjust Lamp

This is a separate tool where the modal adjusts the currently active lamp
instead of adding a new one.
You can find this tool, with a purple lamp icon, right below the add light tool group.

## Mesh and Tube Light Paint

You can also create mesh lights. Note that they use emissive materials,
which may not behave the same in all render engines.
They have similar parameters as the lamp tool, along with a few extra.

**Mesh lights** create a convex shape from the strokes you drew.
This tool has an extra parameter to flatten the hull into a plane.

**Tube lights** turn each stroke into a "tube" of light -
great for neon lighting.
This tool has extra parameters to merge tube vertices by distance (for a smoother tube shape),
and subdivisions for the tube path or its resulting surface.

### Sky Paint

![Drawing onto an environment and painting direction of sky texture](/docs/assets/sky_paint.gif)

You can add either a sun lamp or a sky texture.

There are two options to determine direction: "average" -
which just takes the mean normal of the annotations, like all the other Light Painter tools -
and "occlusion". The latter imitates a sun above the horizon.
For the number of samples given, the operator will iterate over different sun positions
and check how much of your strokes will be lit from that angle.
After iterating over all the samples, the operator will choose the best position
based on how closely it matches the average normal
and the percentage of your strokes hit.

However, this scoring may result in noonday lighting from above.
To give you more control, there is a "Max Sun Elevation" parameter
where you can specify the max elevation of the sun.
This can force the operator to only sample the sun at lower elevations,
giving more dynamic lighting.

## Shadow Paint

![Painting on an environment and creating "cloud" shadows](/docs/assets/shadow_paint.gif)

Flags can be painted to cast shadows on surfaces.
**Note**: you must select lamps to flag before running the tool.
It takes the surfaces drawn and generates makes a convex mesh hull to block the light.
Parameters can be changed such as position,
the flag's color (for bounce lighting) and opacity.

1. First, add the lights.
2. Select the lights you want to flag.
3. Run the Flag Paint tool. Paint surfaces you want darkened.
   These annotations will be considered edges of a convex hull.
4. Finish the tool by pressing Enter. This will add a flag for each light.

Currently, flags for sky textures are not supported.