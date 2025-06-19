import type { Task } from '@/stores/tasks'
import type { AutoArrangeOptions } from '@/stores/settings'

export interface Position {
  x: number
  y: number
}

export interface TaskPosition {
  taskId: number
  position: Position
  size: { width: number; height: number }
}

interface ArrangeContext {
  tasks: Task[]
  containerWidth: number
  containerHeight: number
  options: AutoArrangeOptions
  taskSizes: Map<number, { width: number; height: number }>
}

// 网格排列
export function arrangeGrid(context: ArrangeContext): Record<number, Position> {
  const { tasks, containerWidth, options, taskSizes } = context
  const { spacing, padding, columns = 4 } = options
  
  const positions: Record<number, Position> = {}
  const defaultSize = { width: 200, height: 120 }
  
  let sortedTasks = [...tasks]
  if (options.sortByPriority) {
    sortedTasks.sort((a, b) => a.urgency - b.urgency)
  }
  
  if (options.groupByModule) {
    sortedTasks.sort((a, b) => (a.module_id || 0) - (b.module_id || 0))
  }

  sortedTasks.forEach((task, index) => {
    const row = Math.floor(index / columns)
    const col = index % columns
    const size = taskSizes.get(task.id) || defaultSize
    
    positions[task.id] = {
      x: padding + col * (size.width + spacing),
      y: padding + row * (size.height + spacing)
    }
  })
  
  return positions
}

// 优先级排列 (从上到下，优先级递减)
export function arrangePriority(context: ArrangeContext): Record<number, Position> {
  const { tasks, options, taskSizes } = context
  const { spacing, padding } = options
  
  const positions: Record<number, Position> = {}
  const defaultSize = { width: 200, height: 120 }
  
  // 按优先级分组
  const tasksByPriority = tasks.reduce((acc, task) => {
    if (!acc[task.urgency]) acc[task.urgency] = []
    acc[task.urgency].push(task)
    return acc
  }, {} as Record<number, Task[]>)
  
  let currentY = padding
  
  // P0到P4依次排列
  for (let priority = 0; priority <= 4; priority++) {
    const priorityTasks = tasksByPriority[priority] || []
    if (priorityTasks.length === 0) continue
    
    let currentX = padding
    let maxHeight = 0
    
    priorityTasks.forEach(task => {
      const size = taskSizes.get(task.id) || defaultSize
      positions[task.id] = { x: currentX, y: currentY }
      currentX += size.width + spacing
      maxHeight = Math.max(maxHeight, size.height)
    })
    
    currentY += maxHeight + spacing * 2 // 额外间距区分优先级
  }
  
  return positions
}

// 模块分组排列
export function arrangeModule(context: ArrangeContext): Record<number, Position> {
  const { tasks, options, taskSizes } = context
  const { spacing, padding } = options
  
  const positions: Record<number, Position> = {}
  const defaultSize = { width: 200, height: 120 }
  
  // 按模块分组
  const tasksByModule = tasks.reduce((acc, task) => {
    const moduleId = task.module_id || 0
    if (!acc[moduleId]) acc[moduleId] = []
    acc[moduleId].push(task)
    return acc
  }, {} as Record<number, Task[]>)
  
  let currentY = padding
  
  Object.values(tasksByModule).forEach(moduleTasks => {
    if (moduleTasks.length === 0) return
    
    // 模块内按优先级排序
    if (options.sortByPriority) {
      moduleTasks.sort((a, b) => a.urgency - b.urgency)
    }
    
    let currentX = padding
    let maxHeight = 0
    
    moduleTasks.forEach(task => {
      const size = taskSizes.get(task.id) || defaultSize
      positions[task.id] = { x: currentX, y: currentY }
      currentX += size.width + spacing
      maxHeight = Math.max(maxHeight, size.height)
    })
    
    currentY += maxHeight + spacing * 3 // 额外间距区分模块
  })
  
  return positions
}

// 时间线排列 (按创建时间)
export function arrangeTimeline(context: ArrangeContext): Record<number, Position> {
  const { tasks, options, taskSizes } = context
  const { spacing, padding } = options
  
  const positions: Record<number, Position> = {}
  const defaultSize = { width: 200, height: 120 }
  
  // 按创建时间排序
  const sortedTasks = [...tasks].sort((a, b) => 
    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )
  
  let currentX = padding
  let currentY = padding
  let rowHeight = 0
  const maxRowWidth = context.containerWidth - padding * 2
  
  sortedTasks.forEach(task => {
    const size = taskSizes.get(task.id) || defaultSize
    
    // 换行逻辑
    if (currentX + size.width > maxRowWidth && currentX > padding) {
      currentX = padding
      currentY += rowHeight + spacing
      rowHeight = 0
    }
    
    positions[task.id] = { x: currentX, y: currentY }
    currentX += size.width + spacing
    rowHeight = Math.max(rowHeight, size.height)
  })
  
  return positions
}

// 紧凑排列 (Bin packing算法)
export function arrangeCompact(context: ArrangeContext): Record<number, Position> {
  const { tasks, options, taskSizes } = context
  const { spacing, padding } = options
  
  const positions: Record<number, Position> = {}
  const defaultSize = { width: 200, height: 120 }
  
  // 按面积从大到小排序
  const sortedTasks = [...tasks].sort((a, b) => {
    const sizeA = taskSizes.get(a.id) || defaultSize
    const sizeB = taskSizes.get(b.id) || defaultSize
    return (sizeB.width * sizeB.height) - (sizeA.width * sizeA.height)
  })
  
  const placedRects: Array<{ x: number; y: number; width: number; height: number }> = []
  
  sortedTasks.forEach(task => {
    const size = taskSizes.get(task.id) || defaultSize
    const rect = { x: 0, y: 0, width: size.width, height: size.height }
    
    // 找到最佳位置
    let bestPosition = { x: padding, y: padding }
    let bestScore = Infinity
    
    // 尝试在已放置的矩形旁边放置
    for (const placed of placedRects) {
      const candidates = [
        { x: placed.x + placed.width + spacing, y: placed.y },
        { x: placed.x, y: placed.y + placed.height + spacing }
      ]
      
      for (const candidate of candidates) {
        if (!hasCollision(candidate.x, candidate.y, size.width, size.height, placedRects, spacing)) {
          const score = candidate.x + candidate.y // 偏向左上角
          if (score < bestScore) {
            bestScore = score
            bestPosition = candidate
          }
        }
      }
    }
    
    positions[task.id] = bestPosition
    placedRects.push({
      x: bestPosition.x,
      y: bestPosition.y,
      width: size.width,
      height: size.height
    })
  })
  
  return positions
}

// 径向排列
export function arrangeRadial(context: ArrangeContext): Record<number, Position> {
  const { tasks, containerWidth, containerHeight, options, taskSizes } = context
  const { spacing } = options
  
  const positions: Record<number, Position> = {}
  const defaultSize = { width: 200, height: 120 }
  
  const centerX = containerWidth / 2
  const centerY = containerHeight / 2
  const baseRadius = 150
  
  let sortedTasks = [...tasks]
  if (options.sortByPriority) {
    sortedTasks.sort((a, b) => a.urgency - b.urgency)
  }
  
  sortedTasks.forEach((task, index) => {
    const layer = Math.floor(index / 8) // 每层8个
    const indexInLayer = index % 8
    const angle = (indexInLayer / 8) * 2 * Math.PI
    const radius = baseRadius + layer * (120 + spacing)
    
    const size = taskSizes.get(task.id) || defaultSize
    
    positions[task.id] = {
      x: centerX + radius * Math.cos(angle) - size.width / 2,
      y: centerY + radius * Math.sin(angle) - size.height / 2
    }
  })
  
  return positions
}

// 聚类排列 (基于任务关系和相似性)
export function arrangeCluster(context: ArrangeContext): Record<number, Position> {
  const { tasks, options, taskSizes } = context
  const { spacing, padding } = options
  
  const positions: Record<number, Position> = {}
  const defaultSize = { width: 200, height: 120 }
  
  // 创建任务关系图
  const clusters = createClusters(tasks)
  
  let currentX = padding
  let currentY = padding
  let maxRowHeight = 0
  
  clusters.forEach(cluster => {
    let clusterStartX = currentX
    let clusterMaxHeight = 0
    
    cluster.forEach(task => {
      const size = taskSizes.get(task.id) || defaultSize
      positions[task.id] = { x: currentX, y: currentY }
      currentX += size.width + spacing
      clusterMaxHeight = Math.max(clusterMaxHeight, size.height)
    })
    
    maxRowHeight = Math.max(maxRowHeight, clusterMaxHeight)
    currentX = clusterStartX
    currentY += clusterMaxHeight + spacing * 2 // 集群间距
  })
  
  return positions
}

// 创建任务聚类
function createClusters(tasks: Task[]): Task[][] {
  const clusters: Task[][] = []
  const processed = new Set<number>()
  
  tasks.forEach(task => {
    if (processed.has(task.id)) return
    
    const cluster = [task]
    processed.add(task.id)
    
    // 找相关任务 (同模块、父子关系等)
    tasks.forEach(otherTask => {
      if (processed.has(otherTask.id)) return
      
      const isRelated = 
        task.module_id === otherTask.module_id ||
        task.parent_id === otherTask.id ||
        otherTask.parent_id === task.id ||
        Math.abs(task.urgency - otherTask.urgency) <= 1
      
      if (isRelated) {
        cluster.push(otherTask)
        processed.add(otherTask.id)
      }
    })
    
    clusters.push(cluster)
  })
  
  return clusters
}

// 碰撞检测
function hasCollision(
  x: number,
  y: number,
  width: number,
  height: number,
  placedRects: Array<{ x: number; y: number; width: number; height: number }>,
  spacing: number
): boolean {
  for (const rect of placedRects) {
    if (
      x < rect.x + rect.width + spacing &&
      x + width + spacing > rect.x &&
      y < rect.y + rect.height + spacing &&
      y + height + spacing > rect.y
    ) {
      return true
    }
  }
  return false
}

// 主要的自动排列函数
export function autoArrange(
  tasks: Task[],
  containerWidth: number,
  containerHeight: number,
  options: AutoArrangeOptions,
  taskSizes: Map<number, { width: number; height: number }>
): Record<number, Position> {
  const context: ArrangeContext = {
    tasks,
    containerWidth,
    containerHeight,
    options,
    taskSizes
  }
  
  switch (options.mode) {
    case 'grid':
      return arrangeGrid(context)
    case 'priority':
      return arrangePriority(context)
    case 'module':
      return arrangeModule(context)
    case 'timeline':
      return arrangeTimeline(context)
    case 'compact':
      return arrangeCompact(context)
    case 'radial':
      return arrangeRadial(context)
    case 'cluster':
      return arrangeCluster(context)
    default:
      return arrangeGrid(context)
  }
}