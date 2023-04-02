# Welcome!

Welcome to the official Light Painter documentation!
Here you can learn how to use the Blender add-on and dive into the Python package.

View the repository at [github.com/semagnum/lightpaint](https://github.com/semagnum/lightpaint).


## Painting

![pie menu for annotations](/assets/pie_menu_paint.png)

The painting is done using Blender's
[annotation tools](https://docs.blender.org/manual/en/latest/interface/annotate_tool.html)
in the 3D view.
You can find these in the toolshelf on the left-hand side of the 3D view.
These tools are also provided as a pie menu
(default shortcut is `Ctrl + Shift + P` in the 3D view)
and in the Light Painter panel for convenience.

Regarding the stroke placement setting,
the two options I'd recommend is "3D Cursor" or "Surface".
You can find this setting in the Light Painter panel as well
as in the tool settings of the 3D view header.

Now just paint where you want the light to hit your objects' surfaces!

### What's the best way to paint?

![Adding a light, step by step](/assets/painting_steps.gif)

You do not need to fill _every_ surface with the annotation tool.
Draw some simple strokes over surfaces that you would like highlighted by your light.
Keep in mind that the surface's normal you are annotating
will also influence where the light will be finally positioned.

The tool also works best
when your annotation matches the shape of the type of lamp that you want.

Here are some general painting tips:

- Draw on multiple surfaces, preferably ones facing different directions.
- The operators can handle some cases where the surfaces you paint face different directions,
  but avoid complete opposite directions for better results.
- Spot lamps prefer circular strokes.
  But if you do not trust your drawing ability,
  a painted line representing the diameter is sufficient.
- Area lamps prefer rectangles, squares, circles or a single painted line.
- Point lamps are the most forgiving since a point lamp's rotation is irrelevant.

## Adding lights

![pie menu for adding lights](/assets/pie_menu_light.png)

You can find the light operators as a pie menu
(default shortcut is `Shift + P` in the 3D view)
or in the Light Painter panel.

There are several light types:

- point lamp
- sun lamp
- spot lamp
- area lamp
- world sky texture

Also included are these (but since they use emissive materials,
they will not work the same outside of Eevee):

- emissive mesh object as a convex hull
- emissive tube - each annotation stroke becomes a "tube" of light -
  great for neon lighting or custom-shaped lighting.

You can press `F9` or click the collapsed Redo Panel in the bottom-left corner of the 3D view
to tweak parameters such as light distance, power and color.

**Remember that the operator will use all annotations on
the current frame as part of the evaluation.**
The add-on cannot remove annotations post-operation for you, 
that would prevent the Redo Panel from working
(since it could not redo the operation if the annotations are no longer there).
There is a convenience button in the pie menu and panel
to clear all strokes on the current frame.
So you must create strokes, add a light, clear or erase strokes,
and new strokes to add the next light.

### Sun lamp and Sky texture operators

![Adding sky texture](/assets/sky_texture.gif)

These two have some unique settings, so I will go over that.
There are two options to determine direction: "average" -
which just takes the mean normal of the annotations -
and "occlusion". The latter imitates a sun above the horizon.
For the number of samples given, the operator will iterate over different sun positions
and check how much of your annotation's surface will be hit.
After iterating over all the samples, the operator will choose the best position.

However, this scoring of the best position may result in noonday lighting from above.
To give the artist more control, there is a "Max Sun Elevation" parameter
where you can specify the max elevation of the sun.
This can force the operator to only sample the sun at lower elevations,
giving more dynamic lighting.

```{toctree}
:maxdepth: 3
lightpaint.rst
```