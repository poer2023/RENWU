import { ref, Ref, reactive } from 'vue'
import { type Task } from '@/stores/tasks'

// 拖动类型枚举
enum DragType {
  NONE = 'none',
  CANVAS_PAN = 'canvas_pan',     // 画布平移
  TASK_DRAG = 'task_drag'        // 任务拖动
}

// 拖动状态接口
interface DragState {
  type: DragType
  isActive: boolean
  startX: number
  startY: number
  currentX: number
  currentY: number
  deltaX: number
  deltaY: number
  lastDeltaX: number // 上一帧的增量，用于计算帧间差值
  lastDeltaY: number
  target: HTMLElement | null
  task: Task | null
  button: number // 0=左键, 1=中键, 2=右键
  // 任务拖动专用
  taskStartPosition: TaskPosition | null // 任务拖动开始时的画布坐标
  mouseOffsetX: number // 鼠标相对于任务的偏移
  mouseOffsetY: number
}

// 画布状态接口
interface CanvasState {
  x: number
  y: number
  scale: number
}

// 任务位置接口
interface TaskPosition {
  x: number
  y: number
}

// 配置选项
interface DragSystemOptions {
  onCanvasPanStart?: () => void
  onCanvasPanMove?: (deltaX: number, deltaY: number) => void
  onCanvasPanEnd?: () => void
  onTaskDragStart?: (task: Task) => void
  onTaskDragMove?: (task: Task, position: TaskPosition) => void
  onTaskDragEnd?: (task: Task, position: TaskPosition) => void
  onTaskSelect?: (task: Task | null) => void
}

export function useUnifiedDragSystem(
  canvasContainer: Ref<HTMLElement | undefined>,
  canvas: Ref<CanvasState>,
  taskPositions: Ref<{ [key: number]: TaskPosition }>,
  options: DragSystemOptions = {}
) {
  // 拖动状态
  const dragState = reactive<DragState>({
    type: DragType.NONE,
    isActive: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
    deltaX: 0,
    deltaY: 0,
    lastDeltaX: 0,
    lastDeltaY: 0,
    target: null,
    task: null,
    button: 0,
    taskStartPosition: null,
    mouseOffsetX: 0,
    mouseOffsetY: 0
  })

  // 超高性能优化变量
  let rafId: number | null = null
  let lastFrameTime = 0
  const FRAME_THROTTLE = 8 // 120fps for ultra smooth drag
  let pendingUpdate = false
  
  // 缓存变量减少重复计算
  let cachedContainerRect: DOMRect | null = null
  let rectCacheTime = 0
  const RECT_CACHE_TTL = 100 // 100ms缓存有效期

  // === 核心拖动逻辑 ===

  function startDrag(event: MouseEvent) {
    const target = event.target as HTMLElement
    
    // --- 第一层：忽略明确的UI组件 ---
    const isUIComponent = target.closest(
      '.mini-map, .canvas-controls, .ai-assistant, .dialog, .popover, .dropdown, .el-select, .el-input, .el-button, .fab-menu, .context-toolbar'
    )
    
    if (isUIComponent) {
      console.log('🔧 [UnifiedDrag] 忽略UI组件:', target.className)
      return // 完全不处理，让事件正常传播
    }

    // --- 第二层：检查是否在任务卡片内 ---
    const taskElement = target.closest('.task-wrapper') as HTMLElement
    
    if (taskElement) {
      // 在任务卡片内部，需要更精细的判断
      
      // 🔗 连接端口：优先级最高，直接忽略让连接功能处理
      if (target.closest('.connection-port, .port-dot')) {
        console.log('🔗 [UnifiedDrag] 检测到连接端口点击，交由连接系统处理')
        return
      }
      
      // 📏 缩放手柄：优先级次高，直接忽略让缩放功能处理
      if (target.closest('.resize-handle, .resize-handles')) {
        console.log('📏 [UnifiedDrag] 检测到缩放手柄，交由缩放系统处理')
        return
      }
      
      // 📝 编辑元素：直接忽略让编辑功能处理
      if (target.closest('input, textarea, select, [contenteditable="true"], button, .action-btn, .edit-btn, .delete-btn, .save-btn, .cancel-btn')) {
        console.log('📝 [UnifiedDrag] 检测到编辑元素，交由编辑系统处理')
        return
      }
      
      // 🎯 特殊交互区域：直接忽略
      if (target.closest('.editing-fields, .footer-actions, .editing-actions')) {
        console.log('🎯 [UnifiedDrag] 检测到特殊交互区域，交由对应系统处理')
        return
      }
      
      // 📋 其他情况：检查是否是明确的"不可拖拽"区域
      // 允许在标题上拖拽（但不是在编辑状态）
      const isInEditingMode = taskElement.querySelector('.task-node.editing')
      if (isInEditingMode && target.closest('.node-title, .task-description')) {
        console.log('📋 [UnifiedDrag] 编辑模式下点击文本，交由编辑系统处理')
        return
      }
      
      // 🎯 其他所有情况：允许拖拽任务
      // 这包括：标题区域、内容区域、空白区域等
    }

    // --- 第三层：确定拖拽类型 ---
    
    // 重置基本状态
    dragState.isActive = true
    dragState.startX = event.clientX
    dragState.startY = event.clientY
    dragState.currentX = event.clientX
    dragState.currentY = event.clientY
    dragState.deltaX = 0
    dragState.deltaY = 0
    dragState.lastDeltaX = 0
    dragState.lastDeltaY = 0
    dragState.target = target
    dragState.button = event.button
    dragState.task = null
    dragState.type = DragType.NONE

    // 根据按键和目标确定拖动类型
    if (event.button === 1) { // 中键总是平移画布
      dragState.type = DragType.CANVAS_PAN
      options.onCanvasPanStart?.()
      console.log('🖱️ [UnifiedDrag] 开始中键画布拖拽')
    } else if (event.button === 0 && taskElement) { // 左键在任务上
      // --- 开始任务拖拽 ---
      const taskId = parseInt(taskElement.dataset.taskId || '0', 10)
      const task = findTaskById(taskId)
      if (task) {
        dragState.type = DragType.TASK_DRAG
        dragState.task = task
        dragState.taskStartPosition = taskPositions.value[task.id] || { x: 0, y: 0 }
        
        const containerRect = canvasContainer.value?.getBoundingClientRect()
        if (!containerRect) {
          console.error('❌ [UnifiedDrag] 无法获取画布容器边界')
          dragState.isActive = false
          return
        }
        
        const canvasMouseX = (event.clientX - containerRect.left - canvas.value.x) / canvas.value.scale
        const canvasMouseY = (event.clientY - containerRect.top - canvas.value.y) / canvas.value.scale
        
        dragState.mouseOffsetX = canvasMouseX - dragState.taskStartPosition.x
        dragState.mouseOffsetY = canvasMouseY - dragState.taskStartPosition.y
        
        options.onTaskDragStart?.(task)
        console.log('🎯 [UnifiedDrag] 准备任务拖拽:', task.title)
      } else {
        // 找不到任务，中止
        dragState.isActive = false
        return
      }
    } else {
      // 其他情况（左键点击空白区域、右键等）不处理
      dragState.isActive = false
      return
    }

    // --- 如果我们走到了这里，说明一个有效的拖拽操作即将开始 ---
    
    // 绑定全局事件来处理拖拽过程
    document.addEventListener('mousemove', handleMouseMove, { passive: false })
    document.addEventListener('mouseup', handleMouseUp, { once: true })
    
    // 设置进行中的样式
    document.body.style.userSelect = 'none'
    document.body.style.cursor = dragState.type === DragType.CANVAS_PAN ? 'grabbing' : 'move'
  }

  function handleMouseMove(event: MouseEvent) {
    if (!dragState.isActive) return

    const now = performance.now()
    
    // 优化节流控制 - 降低阈值提高响应性
    if (now - lastFrameTime < FRAME_THROTTLE && !pendingUpdate) {
      return
    }

    // 批量更新位置数据
    dragState.currentX = event.clientX
    dragState.currentY = event.clientY
    dragState.deltaX = dragState.currentX - dragState.startX
    dragState.deltaY = dragState.currentY - dragState.startY

    // 计算移动距离，只有超过阈值才开始真正的拖拽
    const distance = Math.sqrt(dragState.deltaX ** 2 + dragState.deltaY ** 2)
    const DRAG_THRESHOLD = 3 // 进一步降低阈值，提高响应速度
    
    // 只有移动距离超过阈值才开始拖拽行为
    if (distance < DRAG_THRESHOLD) {
      return
    }

    // 🔧 修复: 只在确实需要拖拽时阻止默认行为，并且不阻止所有事件
    if (dragState.type !== DragType.NONE) {
      // 只阻止默认行为，不阻止事件传播
      if (event.cancelable) {
        event.preventDefault()
      }
    }

    // 标记需要更新
    pendingUpdate = true

    // 取消之前的RAF
    if (rafId) cancelAnimationFrame(rafId)

    // 使用RAF批量处理拖动更新
    rafId = requestAnimationFrame(() => {
      if (pendingUpdate && dragState.isActive) {
        if (dragState.type === DragType.CANVAS_PAN) {
          handleCanvasPan()
        } else if (dragState.type === DragType.TASK_DRAG && dragState.task) {
          handleTaskDrag()
        }
        
        pendingUpdate = false
        lastFrameTime = performance.now()
      }
    })
  }

  function handleMouseUp(event: MouseEvent) {
    const wasActive = dragState.isActive
    const type = dragState.type
    const task = dragState.task

    // 如果移动距离很小，视为点击而非拖动
    const distance = Math.sqrt(dragState.deltaX ** 2 + dragState.deltaY ** 2)
    const isClick = distance < 8

    // 🔧 修复7: 改进点击处理逻辑
    if (wasActive && isClick && event.button === 0 && type === DragType.TASK_DRAG && task) {
      // 这是一次点击，但因为我们已经在startDrag中处理了选择，这里不再重复
      console.log('👆 [UnifiedDrag] 点击任务完成:', task.title)
    }

    // 结束回调
    if (wasActive && !isClick) {
      if (type === DragType.CANVAS_PAN) {
        options.onCanvasPanEnd?.()
        console.log('🖱️ [UnifiedDrag] 画布拖拽结束')
      } else if (type === DragType.TASK_DRAG && task) {
        const position = getTaskFinalPosition(task)
        options.onTaskDragEnd?.(task, position)
        console.log('🎯 [UnifiedDrag] 任务拖拽结束:', task.title, position)
      }
    }

    // 清理状态
    cleanup()
  }

  function handleCanvasPan() {
    // 计算帧间增量，避免漂移
    const frameDeltaX = dragState.deltaX - dragState.lastDeltaX
    const frameDeltaY = dragState.deltaY - dragState.lastDeltaY
    
    // 更新上一帧记录
    dragState.lastDeltaX = dragState.deltaX
    dragState.lastDeltaY = dragState.deltaY
    
    options.onCanvasPanMove?.(frameDeltaX, frameDeltaY)
  }

  function handleTaskDrag() {
    if (!dragState.task) return

    const position = getTaskFinalPosition(dragState.task)
    options.onTaskDragMove?.(dragState.task, position)
  }

  function getTaskFinalPosition(task: Task): TaskPosition {
    if (!dragState.taskStartPosition) {
      console.warn('⚠️ [UnifiedDrag] 任务初始位置未设置，使用当前位置')
      return taskPositions.value[task.id] || { x: 0, y: 0 }
    }
    
    // 使用缓存的containerRect提升性能
    const now = performance.now()
    if (!cachedContainerRect || now - rectCacheTime > RECT_CACHE_TTL) {
      cachedContainerRect = canvasContainer.value?.getBoundingClientRect() || null
      rectCacheTime = now
    }
    
    const containerRect = cachedContainerRect
    if (!containerRect) {
      console.error('❌ [UnifiedDrag] 无法获取画布容器边界')
      return dragState.taskStartPosition
    }
    
    const canvasMouseX = (dragState.currentX - containerRect.left - canvas.value.x) / canvas.value.scale
    const canvasMouseY = (dragState.currentY - containerRect.top - canvas.value.y) / canvas.value.scale
    
    // 计算任务的新位置 = 鼠标位置 - 鼠标偏移量
    const newX = canvasMouseX - dragState.mouseOffsetX
    const newY = canvasMouseY - dragState.mouseOffsetY
    
    return {
      x: newX,
      y: newY
    }
  }

  let findTaskById = (id: number): Task | null => {
    // 这里需要注入任务查找逻辑
    // 临时实现，实际使用时需要传入任务列表
    return null
  }

  function cleanup() {
    // 取消RAF和清理性能优化变量
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    
    pendingUpdate = false
    lastFrameTime = 0
    
    // 清理缓存
    cachedContainerRect = null
    rectCacheTime = 0

    // 移除事件监听
    document.removeEventListener('mousemove', handleMouseMove, { capture: false } as any)
    document.removeEventListener('mouseup', handleMouseUp, { capture: false } as any)

    // 恢复样式
    document.body.style.userSelect = ''
    document.body.style.cursor = ''

    // 重置状态
    Object.assign(dragState, {
      type: DragType.NONE,
      isActive: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
      deltaX: 0,
      deltaY: 0,
      lastDeltaX: 0,
      lastDeltaY: 0,
      target: null,
      task: null,
      button: 0,
      taskStartPosition: null,
      mouseOffsetX: 0,
      mouseOffsetY: 0
    })
  }

  // === 公共接口 ===

  function init(taskList: Ref<Task[]>) {
    if (!canvasContainer.value) return

    console.log('🔧 [UnifiedDrag] 初始化统一拖动系统 v2.0')

    // 重写findTaskById
    findTaskById = (id: number) => {
      return taskList.value.find(task => task.id === id) || null
    }

    // 🔧 修复8: 使用更合理的事件绑定方式
    canvasContainer.value.addEventListener('mousedown', startDrag, { 
      passive: false, 
      capture: false // 不使用捕获，让TaskCard事件先处理
    })

    console.log('✅ [UnifiedDrag] 统一拖动系统v2.0初始化完成')
  }

  function destroy() {
    console.log('🔧 [UnifiedDrag] 销毁统一拖动系统')
    
    cleanup()

    if (canvasContainer.value) {
      canvasContainer.value.removeEventListener('mousedown', startDrag, { capture: false } as any)
    }
  }

  return {
    dragState,
    init,
    destroy,
    isCanvasPanning: () => dragState.type === DragType.CANVAS_PAN && dragState.isActive,
    isTaskDragging: () => dragState.type === DragType.TASK_DRAG && dragState.isActive,
    getCurrentDragTask: () => dragState.task
  }
}