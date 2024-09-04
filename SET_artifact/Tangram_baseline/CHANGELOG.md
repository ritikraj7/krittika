List of major changes and improvements
======================================

## [v2.0 -- v2.1] -- 2010-12-31

### Added

- Workload models.

  - Add ResNet-50.

- Software engineering.

  - Port code to Python 3; drop Python 2 support.

  - Add pylintrc.


### Changed

- Software models.

  - Share the same partition between input layer and external layers. For
    layered LSTMs, the number of external layers could be quite a few (e.g.,
    8). The complete combination of all partition choices of these external
    layers is too high to explore. So we assume all input and external layers
    share the same partition scheme.

- Software engineering.

  - Allow both relative and absolute overheads in `approx_dividable`.


## Fixed

- In `LoopBlockingScheme`, put weight-pinning code block after buffer sharing.


## [v1.6 -- v2.0] -- 2018-03-01

### Added

- Hardware models.

  - Access forwarding.

  - Buffer sharing scheme.
    - Use `BufShrScheme` class to represent and calculate NoC transfers.

- Software models.

  - Add `SchedulingConstraint` class to specify loop blocking and partitioning
    constraints.
    - Add lazily updated rules to allow refine constraint with previous
      scheduling results at runtime.
    - Add subclass `SchedulingConstraintLayerPipeline` for layer pipelining
      constraints.

  - Add `InterLayerPipeline`.
    - Layers are organized into `PipelineSegment`, which are simultaneously
      mapped on to the resource both spatially and temporally.
    - Each layer in the segment has a 3-tuple scheduling index including
      segment index, spatial index, and temporal index.
    - Each layer in the segment has its resource allocation and scheduling
      constraint.
    - Use `PipelineSegmentTiming` to capture the timing relation of layers in
      the segment.
    - Specify maximum allowed execution time overhead due to layer pipelining
      in `Option`.
    - Specify maximum pipelining degree for layer pipelining in `Option`.

  - Add layer pipelining optimizations.
    - Ofmap forwarding: alternate layer loop ordering.
    - Ifmap forwarding: sharing the same inputs from memory to multiple
      regions.
    - Support model weight pinning when no resource time-multiplexing.
    - Allow disabling optimizations for layer pipelining to fall back to basic
      pipelining techniques.


### Changed

- Hardware models.

  - Allow data source/destination regions in `Resource` to be non-DATA type.

  - Allow `NodeRegion` to be folded along the w dimension in a zig-zag manner.

- Software models.

  - `LoopBlockingScheme` supports access forwarding and buffer sharing.

  - `LoopBlockingScheme` supports remote node buffers as data regions (non-data
    type data regions).

  - `partition` unit number of hops calculation supports access forwarding and
    buffer sharing.

  - `DataLayout` supports closest-first forwarding data transfer for access
    forwarding and buffer sharing.

  - Refactor `NNDataflow` and `NNDataflowScheme` to incorporate inter-layer
    pipelining.


## [v1.5 -- v1.6] -- 2018-01-31

### Added

- Workload models.

  - Add `EltwiseLayer`.

  - Allow only concatenation of layers; summation of layers turns into an
    additional `EltwiseLayer`.

  - Add external layers to networks, which is external directly input data.

  - Add various LSTMs.

  - Add `data_loops` attribute with type `DataDimLoops` to each type of layer.

- Hardware models:

  - Add DRAM region in `Resource`.

  - Consider array bus width and its impact on data multicast latency.

  - Consider DRAM access time due to bandwidth limit.

- Software models.

  - Add choices for optimization goal: E(nergy), D(elay), or ED.

- Software engineering.

  - Record search time.

  - Add utility `IntRange` for integer ranges.

  - Add `HashableDict` class.


### Changed

- Hardware models.

  - 2D memory type is changed to constant four node on the chip corners.

  - `NodeRegion` adds `dist` attribute for inter-node distance.

  - `NodeRegion` renames `DATA` enum to `DRAM`.

  - Limit to single source/destination data regions in `Resource`.

- Software models.

  - `Cost` uses static/idle unit cost for all nodes instead of one node.

  - `Scheduling` breaks loop/part cost into op/access/noc/static cost.

  - `Scheduling` breaks cost tie using time, using a compare key function of
    `SchedulingResult`.

  - Add external occupancy to `MapStrategy` and merge into `NestedLoopDesc`;
    use it for partitioning occupancy.

  - `FmapRange.beg_end()` returns an `IntRange` instance if with a single
    attribute argument, or a list of `IntRange` otherwise.

  - Move partitioning scheme sub-`FmapRange` method, which is used to get
    partitioned fmap ranges, to `PartitionScheme`.

  - Move partitioning scheme projection, which is used to generate ofmap
    layout, to `PartitionScheme`.

  - `DataLayout` refactored: use `PartitionScheme` to replace `FmapRangeMap`.

  - `partition` module refactored: use new `DataLayout` class and new
    `PartitionScheme` methods.

  - `SchedulingResult` uses a combined `OrderedDict` to replace `dict_loop` and
    `dict_part`.

  - In partitioning schemes, each partitioning must fully utilize one dimension
    before starting the other, except for fmap partitioning.

- Software engineering.

  - Change `NNDataflowScheme` node-time product interface to explicitly be
    static cost.

  - Improve method names:
    - Remove `DataDimLoops.data_cnt`.
    - Change `NodeRegion.node_iter` to `NodeRegion.iter_node`.
    - Change `Network` method names to distinguish layer and layer name.


### Fixed

- Output dict `PartitionScheme` format fix.

- `idivc` with inf arguments.

- Integer division `//` vs. `/`.

- ITCN access calculation for unit pass in `MapStrategy`.

- `FmapRange` comparison.

- Unit nhops calculation for filter data uses DRAM region.

- Unit nhops calculation considers nodes with both non-empty ifmaps and ofmaps.

- Replication size when underutilizing PE arrays.


## [v1.4 -- v1.5] -- 2017-08-18

### Added

- Workload models.

  - `Network` method to return next layers.

  - `Network` uses `None` in previous/next layers for the input/output layers.

  - `Network` methods to return the first/last layers.

  - Add batch size argument to layer fmap size methods.

  - Add default filter size to `FCLayer`.

  - Add `DataDimLoops` class to denote loops that are dimensions of a data
    category.

  - Add neural neworks: MLP-L/M/S from PRIME ISCA 2016.

- Software models.

  - Add statistic properties to `SchedulingResult`.

  - Add `NNDataflowScheme` class for overall NN dataflow.

- Software engineering.

  - Add utilities to `LoopBlockingScheme` class.

  - Add negative operation to `PhyDim2`.

  - Add default arguments to `Option`.

- Test.

  - Add unit tests.


### Changed

- Workload models.

  - Relax `__len__` of `Network` to work before setting input layer.

  - Allow different height and width for filters in `ConvLayer`.

- Hardware models:

  - Upgrade node dimensions to node region in `Resource`. The origins of node
    region and memory regions are all absolute.

  - Add `type` attribute to `NodeRegion` to differentiate processing and data
    node regions in `Resource`.

  - Change default cost of the NoC hop traversal.

- Software models:

  - Add loop index generator to `LoopBlockingScheme` class.

  - PE array mapping for `LocalRegionLayer` reduces regfile size.

  - Loop blocking scheme result stats change from one node to all nodes.

  - Move partition occupation into `LoopBlockingScheme` constructor.

  - Move `LoopBlockingScheme` verification to tests.

  - Improve the workload partitioning for loop blocking exhaustive search.

  - Merge `loopcnt` attribute of `NestedLoopDesc` to a tuple.

  - Change `LoopBlockingScheme` interface for blocking factors and loop orders.

  - Loop blocking exhaustive search introduces regularized schemes and
    suboptimal schemes, to enable more skips. Also restrict the skips to CONV
    layer.

  - Refactor loop blocking bypass solvers, and restrict it to CONV layer.

  - Use row-stationary mapping to `LocalRegionLayer`, and merge with that of
    `ConvLayer`.

  - Generalize `LoopBlockingScheme` access model for arbitrary data loops.

  - Skip equivalence when generating `PartitionScheme`.

  - Check ifmap layout against layer parameters in `Scheduling`.

  - Add number of nodes to scheduling result.

  - Add `type` attribute to `DataLayout` to denote the type of the reside
    region.

  - Add guarantee to generate `PartitionScheme`.

- Software engineering.

  - Lazily evaluate loop blocking stats.

  - Use rich comparison instead of `__cmp__`.

  - Convert `RuntimeError` exceptions to assertions.

  - Define `__repr__` for class stringify, and remove `StringifyClass`.

  - Move map strategy class into `NNDataflow` constructor.

  - Reorganize package structure.

  - Use lower-case name for all modules.

  - Add local version number to output.


### Fixed

- Output data fetch count.

- Error types and message typos.

- `FmapRange` comparison: overlapping ranges cannot compare.

- Multiple bugs fixed in `Util`.

- Multiple bugs fixed in `PartitionScheme`.

- Use GBUF unit access for DRAM when bypassing GBUF.

- Partitioned ifmap range for `LocalRegionLayer`.

- Clarify ITCN accesses to be number of individual transfers to each REGF.

- `Partition` unit number of hops calculation ignores zero-sized data ranges.


## [v1.3 -- v1.4] -- 2017-05-18

### Added

- Software models.

  - Partition schemes.
    - Input partitioning: partition different input fmaps (channels).

- Explorers and solvers:

  - Loop blocking exhaustive search skips more equivalent schemes.
    - Adjacent same loops in different hierarchy levels.

- Software engineering

  - Verbose mode.


### Changed

- Software models:

  - Loop blocking.
    - Avoid initial zero-value fetch for output data.

- Software engineering.

  - Use a single global argument parser.

  - Introduce ContentHashClass.


### Fixed

- FmapRange comparison.

- Map strategy bug when filters are folded.


## [v1.2 -- v1.3] -- 2017-05-16

### Added

- Workload models:

  - Support loops: ifmap channel loop, ofmap channel loop, batch loop.

- Software models:

  - Loop index generator for different loop blocking schemes.

  - Debug mode:
    - Verification of the loop blocking access model.

- Explorers and solvers:

  - Loop blocking exhaustive search skips equivalent schemes.


### Changed

- Software models:

  - Loop blocking data buffer and reuse models.
    - Loop orders now also consider the order of batch loop.
    - Change the model for trivial loops (with blocking factor 1).


## [v1.1 -- v1.2] -- 2017-05-10

### Added

- Explorers and solvers.

  - Performance improvements.
    - Add loop blocking scheme cache in Scheduling.
    - Use a single Scheduling instance for all same layers.

- Software engineering

  - Class instance used as dict key.
    - Add value-based equality and hash to Layer.
    - Add value-based equality and hash to PartitionScheme.

  - Add version number to output json dump.


### Changed

- Explorers and solvers:

  - Better formatting of verification results against Eyeriss.

- Software engineering

  - Replace numpy for better performance.

  - Move multiprocessing into loop blocking exploration for better performance
    scaling.


## [v1.0 -- v1.1] -- 2017-05-04

### Added

- Workload models.

  - `Network`: a DAG of layers, rather than a linear pipeline.

  - New layer types: pooling layer (local region layer).

  - Enforce layer chaining has matched data size.

  - New neural network: GoogLeNet.

- Hardware models.

  - `NodeRegion`.
    - Used to denote memory regions, i.e., relative positions and sizes of
      memories to the computation node NoC.
    - Support 2D memories, which are on the edges of the chip.

- Software models.

  - `FmapPosition` and `FmapRange`: a position and a range in batched fmaps.
    - `FmapRangeMap`: efficient map structure of `FmapPosition` type.

  - `DataLayout`: describes the layer i/ofmap data layout.
    - Use a `FmapRangeMap` to map each data element to the stored node.

  - Partition schemes.
    - Batch partitioning: partition input data within a batch.

- Explorers and solvers.

  - `SchedulingResultDict`: store layer scheduling results of a network.

  - More checks to enforce the schedules have the correct number of operations
    as the given workloads.


### Changed

- Workload models.

  - Update all network structures to include pooling layers.

- Software models.

  - Allow different partitioning factor along height and width of a fmap, i.e.,
    allow different height and width sizes of the partitioned fmap.

- Explorers and solvers.

  - `NNDataflow`: new top-level class.

- Software engineering:

  - Significant code refactoring to improve modularity.
    - More classes, e.g., `MapStrategy`, `LoopBlockingScheme`, `Scheduling`.

  - Code style lint.

  - Update option names to be more uniform.

  - Standardize class stringify.


### Deprecated

- Option `--hybrid_partition2d`, now is `--hybrid_partition`.


### Fixed

- Use of `map()` function in `PhyDim2`.

- Name of `namedtuple` sublasses.

- Structure configuration of ResNet152.


## [init -- v1.0] -- 2017-01-21

### Added

- Workload models:

  - Two layer types: convolutional layer and fully-connected layer.

  - Supported neural neworks: AlexNet, VGG, VGG19, ZFNet, ResNet152.

  - Supported data categories: ifmaps, ofmaps, and weights.

- Hardware models:

  - 2D Network-on-Chip (NoC) on the PE array (node) level.

  - 2D PE array on the PE level.

  - Memory hierarchy:
    - regf: register file in a PE.
    - itcn: interconnect between PEs in an array.
    - gbuf: global buffer of an array.
    - dram: main memory.

  - Cost (energy) of computation operations (MAC, etc.), memory hierarchy
    accesses, NoC hop traversals, and static leakage.

- Software models:

  - Eyeriss Row-Stationary mapping to PE array (Chen et al., ISCA 2016).

  - Loop blocking schemes over ifmap channel, ofmap channel, and batch loops.
    - Loop reordering: exchange loop order.
    - Loop blocking: split a loop into multiple ones.

  - Partition schemes to split the workload of a layer to different nodes.
    - Fmap partitioning: partition height/width of a fmap.
    - Output partitioning: partition different fmaps (channels).

- Explorers and solvers:

  - Per-layer schedule exploration.

  - Exhaustive search loop blocking schemes and partitioning schemes.

  - Analytically solve bypass loop ordering (Gao et al., ASPLOS 2017).

  - Naive partitioning scheme (Kim et al., ISCA 2016).

- Software engineering

  - Support multi-process parallel processing.

