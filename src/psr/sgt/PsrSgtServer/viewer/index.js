var svg = d3.select("svg");
var width = +svg.attr("width");
var height = +svg.attr("height");

svg.append("rect")
    .attr("width", width)
    .attr("height", height)
    .style("fill", "none")
    .style("pointer-events", "all")
    .call(d3.zoom().scaleExtent([1 / 2, 4]).on("zoom", zoomed));

var g = svg.append("g").attr("class", "graph");
var links = g.append("g").attr("class", "links")
var nodes = g.append("g").attr("class", "nodes")

function zoomed() {
    g.attr("transform", d3.event.transform);
}

var graph = null;

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().distance(30).id(function(d) { return d.id; }))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2));

var stepIdx = 0;

var link;
var outer;
var inner;
var idxLabel;

d3.json("viewer.json", function(error, g) {
    graph = g;
    if (error) throw error;

    var linkG = links.selectAll("g").data(graph.links).enter().append("g");

    link = linkG.append("line");
    linkG.append("line");
    
    var nodeG = nodes.selectAll("g").data(graph.nodes).enter().append("g");
    nodeG.append("line")
        .attr("x1", 0) 
        .attr("x2", 0) 
        .attr("y1", 0)
        .attr("y2", 12)
        .attr("stroke-width", 1.5)
        .attr("stroke", "blue")
        .attr("visibility", function(d) {return d.hasLoad ? "visible" : "hidden";});
    nodeG.append("line")
        .attr("x1", 0) 
        .attr("x2", 0) 
        .attr("y1", -12)
        .attr("y2", 0)
        .attr("stroke-width", 1.5)
        .attr("stroke", "red")
        .attr("visibility", function(d) {return d.hasGen ? "visible" : "hidden";});
    outer = nodeG.append("circle")
        .attr("class", "outer")
        .attr("r", 6)
    inner = nodeG.append("circle")
        .attr("class", "inner")
        .attr("visibility", "hidden") // Comment to see fed state constraint.
        .attr("r", 2)
        .attr("stroke", "white")
        .attr("stroke-width", 1);
    nodeG.append("text")
        .html(function(d) {return d.id;})
        .attr("style", "font-size: 4pt;")
        .attr("text-anchor", "left")
        .attr("alignment-baseline", "middle")
        .attr("x", 8)
        .attr("y", 0);

    idxLabel = d3.select("#idx-label")

    nodeG.call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    link.append("title").text(function(d) { return d.id; });

    nodeG.append("title").text(function(d) { return d.id; });

    dataUpdated();

    simulation
        .nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    function ticked() {
        link
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        nodeG
            .attr("transform", function(d) {return "translate(" + d.x + ", " + d.y + ")"; });
    }
});

function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function dataUpdated() {
    var colors = ["#f0f0f0", "lightgreen", "orange"];

    link
        .attr("stroke", function(d) {
            var col = colors[d.closedStateConstr[stepIdx]];
            return col;
        })
        .attr("stroke-width", function(d) {
            return d.hasBreaker ? 3 : 1.5;
        })

    outer
        .attr("fill", function(d) {
            var col = colors[d.isFed[stepIdx]];
            return col;
        })
        .attr("stroke", function(d) {
            return d.hasFault ? "red" : d.finalRequireFed ? "black" : "white";
        });

    inner
        .attr("fill", function(d) {
            var col = colors[d.fedStateConstr[stepIdx]];
            return col;
        });

    idxLabel
        .html(stepIdx);
}

function step(i) {
    stepIdx = (stepIdx + i + graph.nodes[0].isFed.length) % graph.nodes[0].isFed.length;
    dataUpdated();
}
