#target illustrator

var folder = Folder.selectDialog("Choisis le dossier contenant les fichiers AI");
if (folder == null) exit();


var files = folder.getFiles("*.ai");

for (var i = 0; i < files.length; i++) {
    var doc = app.open(files[i]);

    var artboard = doc.artboards[0];
    var ab = artboard.artboardRect;

    var bgLayer = doc.layers.add();
    bgLayer.name = "Fond blanc";
    bgLayer.zOrder(ZOrderMethod.SENDTOBACK);

    var rect = bgLayer.pathItems.rectangle(
        ab[1],
        ab[0],
        ab[2] - ab[0],
        ab[1] - ab[3]
    );

    rect.filled = true;
    rect.fillColor = new RGBColor();
    rect.fillColor.red = 255;
    rect.fillColor.green = 255;
    rect.fillColor.blue = 255;
    rect.stroked = false;

    doc.save();
    doc.close();
}

alert("Fond blanc ajouté à tous les fichiers.");
