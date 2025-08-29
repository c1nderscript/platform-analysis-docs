---
status: done
source_path: N/A
last_scanned: "2025-08-29T12:50:00Z"
tags: [chat, room-state, synchronization, caching, performance, real-time]
links:
  - "[[chatroom-navigation]]"
  - "[[../Backend/chat]]"
  - "[[../../../../RUST CONVERSION/Components/Chat-Service]]"
category: "Essential"
migration_priority: "Critical"
reuse_potential: "85%"
---

# Room State Management Architecture

## Overview

**Purpose**: Detailed technical specification for managing state synchronization, caching, and real-time updates across multiple chatrooms in a multi-room navigation system.

**Category**: Essential  
**Migration Priority**: Critical  
**Cross-Platform Reuse**: 85%

This document provides the implementation details for efficient room state management that enables seamless navigation between chatrooms while maintaining consistent, up-to-date state information across all rooms.

## State Management Architecture

### Room State Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                  Room State Layers                      │
├─────────────────┬─────────────────┬─────────────────────┤
│   Active State  │  Background     │   Cached State      │
│   (Full)        │  State (Lite)   │   (Minimal)         │
│                 │                 │                     │
│ • Full Messages │ • Presence      │ • Basic Info        │
│ • User Lists    │ • Notifications │ • Last Activity     │
│ • Moderation    │ • Room Config   │ • User Count        │
│ • Real-time     │ • Limited Msgs  │ • Offline Storage   │
└─────────────────┴─────────────────┴─────────────────────┘
```

### State Transition Model

```rust
// Room state lifecycle management
// ANNOTATION: Core enum defining the hierarchical state levels for chatrooms
// Each level represents a different resource allocation and functionality tier
// Active: Full featured state for primary room, Background: Lightweight monitoring state
// Cached: Minimal state for recently visited rooms, Unloaded: Identity only
#[derive(Debug, Clone)]
pub enum RoomStateLevel {
    Active {
        // Full state for currently viewed room
        messages: Vec<Message>,
        users: HashMap<UserId, UserState>,
        moderation_config: ModerationConfig,
        real_time_connection: WebSocketConnection,
        ui_state: UIState,
    },
    Background {
        // Lightweight state for subscribed rooms
        presence_count: u32,
        notifications: Vec<Notification>,
        room_config: RoomConfig,
        limited_messages: CircularBuffer<Message>,
        heartbeat_connection: Option<WebSocketConnection>,
    },
    Cached {
        // Minimal state for recently visited rooms
        basic_info: RoomBasicInfo,
        last_activity: DateTime<Utc>,
        user_count_snapshot: u32,
        stored_locally: bool,
    },
    Unloaded {
        // No state, only room identifier
        room_id: RoomId,
    },
}
```

## State Synchronization Mechanisms

### Real-Time Sync Protocol

#### WebSocket Message Format
```json
{
  "room_state_sync": {
    "message_type": "STATE_UPDATE|BULK_SYNC|DELTA_UPDATE|HEARTBEAT",
    "room_id": "streamer123",
    "timestamp": "2025-08-29T12:50:00Z",
    "sequence_number": 12345,
    "data": {
      // Payload varies by message type
    }
  }
}
```

#### State Update Types
```json
{
  "STATE_UPDATE": {
    "room_config": {
      "slow_mode_enabled": true,
      "slow_mode_duration": 30,
      "subscriber_only": false,
      "follower_only": true,
      "emote_only": false
    },
    "user_count": 15420,
    "moderator_count": 12,
    "stream_status": "live"
  },
  
  "BULK_SYNC": {
    "messages": [
      {
        "id": "msg_123",
        "user": "viewer1",
        "content": "Hello chat!",
        "timestamp": "2025-08-29T12:49:30Z",
        "badges": ["subscriber"]
      }
    ],
    "users": [
      {
        "id": "user_456",
        "username": "viewer1",
        "badges": ["subscriber", "vip"],
        "color": "#FF0000"
      }
    ]
  },
  
  "DELTA_UPDATE": {
    "added_messages": ["msg_124", "msg_125"],
    "removed_messages": ["msg_120"],
    "updated_users": {
      "user_456": {
        "badges": ["subscriber", "vip", "moderator"]
      }
    }
  }
}
```

### Backend State Management (Rust)

#### State Manager Actor
```rust
// ANNOTATION: Central state management actor using Rust's actor model
// Handles state transitions, caching, and real-time synchronization across rooms
// Maintains different levels of room state and provides efficient state promotion/demotion
#[derive(Debug)]
pub struct RoomStateManager {
    rooms: HashMap<RoomId, RoomState>,
    state_cache: LruCache<RoomId, CachedRoomState>,
    sync_connections: HashMap<RoomId, Vec<WebSocketConnection>>,
    update_subscribers: HashMap<RoomId, Vec<UserId>>,
    metrics: StateMetrics,
}

impl RoomStateManager {
    // Promote room from background to active state
    pub async fn promote_room_state(&mut self, 
        room_id: &RoomId,
        user_id: &UserId
    ) -> Result<RoomStateLevel, StateError> {
        
        let current_state = self.rooms.get(room_id);
        
        match current_state {
            Some(RoomState::Background(bg_state)) => {
                // Upgrade background to active
                let active_state = self.expand_to_active_state(room_id, bg_state).await?;
                
                // Establish real-time connection
                let ws_connection = self.establish_realtime_connection(room_id, user_id).await?;
                
                // Update state registry
                self.rooms.insert(room_id.clone(), RoomState::Active(ActiveRoomState {
                    messages: active_state.messages,
                    users: active_state.users,
                    moderation_config: active_state.moderation_config,
                    real_time_connection: ws_connection,
                    ui_state: UIState::default(),
                }));
                
                Ok(RoomStateLevel::Active { /* ... */ })
            },
            Some(RoomState::Cached(cached_state)) => {
                // Load from cache and promote to active
                self.load_from_cache_to_active(room_id, cached_state, user_id).await
            },
            None => {
                // Cold load - fetch from backend
                self.cold_load_room_state(room_id, user_id).await
            },
            _ => {
                // Already active or invalid state transition
                Err(StateError::InvalidStateTransition)
            }
        }
    }
    
    // Demote room from active to background state
    pub async fn demote_room_state(&mut self, 
        room_id: &RoomId,
        keep_notifications: bool
    ) -> Result<(), StateError> {
        
        if let Some(RoomState::Active(active_state)) = self.rooms.remove(room_id) {
            // Compress to background state
            let background_state = BackgroundRoomState {
                presence_count: active_state.users.len() as u32,
                notifications: if keep_notifications { 
                    active_state.extract_notifications() 
                } else { 
                    Vec::new() 
                },
                room_config: active_state.moderation_config.into(),
                limited_messages: active_state.messages
                    .into_iter()
                    .rev()
                    .take(50)  // Keep last 50 messages
                    .collect(),
                heartbeat_connection: Some(
                    active_state.real_time_connection.downgrade_to_heartbeat().await?
                ),
            };
            
            // Update state registry
            self.rooms.insert(room_id.clone(), RoomState::Background(background_state));
            
            // Schedule cache persistence
            self.schedule_cache_persistence(room_id, &active_state).await?;
        }
        
        Ok(())
    }
    
    // Handle real-time state updates
    pub async fn handle_state_update(&mut self, 
        room_id: &RoomId,
        update: StateUpdate
    ) -> Result<(), StateError> {
        
        let current_state = self.rooms.get_mut(room_id);
        
        match (current_state, update) {
            (Some(RoomState::Active(ref mut state)), StateUpdate::Message(msg)) => {
                // Add message to active room
                state.messages.push(msg.clone());
                
                // Maintain message buffer size
                if state.messages.len() > 1000 {
                    state.messages.remove(0);
                }
                
                // Broadcast to subscribers
                self.broadcast_update(room_id, &StateUpdate::Message(msg)).await?;
            },
            
            (Some(RoomState::Background(ref mut state)), StateUpdate::Notification(notif)) => {
                // Add notification to background room
                state.notifications.push(notif.clone());
                
                // Maintain notification buffer
                if state.notifications.len() > 100 {
                    state.notifications.remove(0);
                }
                
                // Notify subscribers
                self.notify_subscribers(room_id, &notif).await?;
            },
            
            _ => {
                // Invalid state/update combination - log and ignore
                warn!("Invalid state update for room {} in state {:?}", 
                      room_id, current_state);
            }
        }
        
        // Update metrics
        self.metrics.record_state_update(room_id, &update);
        
        Ok(())
    }
}
```

#### Caching Strategy
```rust
#[derive(Debug, Clone)]
pub struct CachedRoomState {
    room_id: RoomId,
    basic_info: RoomBasicInfo,
    message_snapshot: Vec<Message>,  // Last N messages
    user_snapshot: Vec<UserId>,      // Recent user list
    config_snapshot: RoomConfig,     // Last known configuration
    cache_timestamp: DateTime<Utc>,
    cache_version: u32,
    serialized_size: usize,
}

impl CachedRoomState {
    // Intelligent cache eviction based on usage patterns
    pub fn should_evict(&self, current_time: DateTime<Utc>) -> bool {
        let age = current_time - self.cache_timestamp;
        let base_ttl = Duration::minutes(30);
        
        // Extend TTL based on access patterns
        let extended_ttl = match self.access_frequency() {
            AccessFrequency::High => base_ttl * 3,      // 90 minutes
            AccessFrequency::Medium => base_ttl * 2,    // 60 minutes  
            AccessFrequency::Low => base_ttl,           // 30 minutes
        };
        
        age > extended_ttl
    }
    
    // Smart cache warming for likely navigation targets
    pub async fn warm_cache_for_user(&self, 
        user_id: &UserId,
        navigation_history: &[RoomId]
    ) -> Result<Vec<RoomId>, CacheError> {
        
        // Predict likely navigation targets
        let prediction = self.predict_navigation_targets(user_id, navigation_history);
        
        let mut warmed_rooms = Vec::new();
        
        for room_id in prediction.high_probability_rooms {
            if !self.is_cached(&room_id) {
                self.preload_room_state(&room_id).await?;
                warmed_rooms.push(room_id);
            }
        }
        
        Ok(warmed_rooms)
    }
}
```

### Frontend State Management (React/TypeScript)

#### State Management Hook
```typescript
// Room state management with React
// ANNOTATION: React hook providing state management functionality for room navigation
// Handles state transitions, real-time updates, and predictive caching
// Integrates with backend state manager for consistent state synchronization
export const useRoomStateManager = () => {
  const [roomStates, setRoomStates] = useState<Map<string, RoomStateLevel>>(new Map());
  const [stateTransitions, setStateTransitions] = useState<Map<string, 'loading' | 'ready' | 'error'>>(new Map());
  
  // State promotion (background -> active)
  const promoteRoomState = useCallback(async (roomId: string) => {
    setStateTransitions(prev => new Map(prev.set(roomId, 'loading')));
    
    try {
      // Request state promotion from backend
      const promotedState = await chatService.promoteRoomState({
        roomId,
        targetLevel: 'active',
        options: {
          loadMessageHistory: true,
          establishRealTimeConnection: true,
          loadUserList: true
        }
      });
      
      // Update local state
      setRoomStates(prev => new Map(prev.set(roomId, promotedState)));
      setStateTransitions(prev => new Map(prev.set(roomId, 'ready')));
      
      // Start real-time sync
      startRealTimeSync(roomId, promotedState.connection);
      
    } catch (error) {
      setStateTransitions(prev => new Map(prev.set(roomId, 'error')));
      throw error;
    }
  }, []);
  
  // State demotion (active -> background)
  const demoteRoomState = useCallback(async (
    roomId: string, 
    options: { keepNotifications: boolean } = { keepNotifications: true }
  ) => {
    const currentState = roomStates.get(roomId);
    if (currentState?.level !== 'active') return;
    
    try {
      // Request state demotion
      const demotedState = await chatService.demoteRoomState({
        roomId,
        targetLevel: 'background',
        preserveNotifications: options.keepNotifications
      });
      
      // Update local state
      setRoomStates(prev => new Map(prev.set(roomId, demotedState)));
      
      // Downgrade connection to heartbeat-only
      downgradeConnection(roomId, currentState.connection);
      
    } catch (error) {
      console.error('Failed to demote room state:', error);
      // Continue with local demotion as fallback
      demoteStateLocally(roomId);
    }
  }, [roomStates]);
  
  // Real-time state synchronization
  const handleStateUpdate = useCallback((roomId: string, update: StateUpdate) => {
    setRoomStates(prev => {
      const currentState = prev.get(roomId);
      if (!currentState) return prev;
      
      const updatedState = applyStateUpdate(currentState, update);
      return new Map(prev.set(roomId, updatedState));
    });
  }, []);
  
  // Predictive cache warming
  const warmCacheForNavigation = useCallback(async (
    currentRoomId: string,
    navigationHistory: string[]
  ) => {
    try {
      const predictions = await chatService.predictNavigationTargets({
        currentRoom: currentRoomId,
        history: navigationHistory,
        userPreferences: getUserPreferences()
      });
      
      // Pre-warm cache for high probability targets
      for (const roomId of predictions.highProbability) {
        if (!roomStates.has(roomId)) {
          // Pre-load minimal state in background
          chatService.preloadRoomState(roomId, 'cached').catch(error => {
            console.warn(`Failed to pre-warm cache for ${roomId}:`, error);
          });
        }
      }
      
    } catch (error) {
      console.warn('Cache warming failed:', error);
    }
  }, [roomStates]);
  
  return {
    roomStates,
    stateTransitions,
    promoteRoomState,
    demoteRoomState,
    handleStateUpdate,
    warmCacheForNavigation,
    getRoomState: (roomId: string) => roomStates.get(roomId),
    isRoomReady: (roomId: string) => stateTransitions.get(roomId) === 'ready'
  };
};
```

#### State Update Handling
```typescript
// Efficient state update application
const applyStateUpdate = (
  currentState: RoomStateLevel, 
  update: StateUpdate
): RoomStateLevel => {
  switch (update.type) {
    case 'MESSAGE_ADDED':
      if (currentState.level === 'active') {
        return {
          ...currentState,
          messages: [...currentState.messages, update.message].slice(-1000), // Keep last 1000
          lastActivity: new Date()
        };
      } else if (currentState.level === 'background') {
        return {
          ...currentState,
          notifications: currentState.notifications.some(n => n.type === 'mention') 
            ? [...currentState.notifications, createNotificationFromMessage(update.message)]
            : currentState.notifications,
          lastActivity: new Date()
        };
      }
      break;
      
    case 'USER_JOINED':
      if (currentState.level === 'active') {
        return {
          ...currentState,
          users: new Map(currentState.users.set(update.user.id, update.user)),
          userCount: currentState.userCount + 1
        };
      }
      break;
      
    case 'ROOM_CONFIG_CHANGED':
      return {
        ...currentState,
        roomConfig: { ...currentState.roomConfig, ...update.configChanges },
        lastConfigUpdate: new Date()
      };
      
    default:
      console.warn('Unknown state update type:', update.type);
  }
  
  return currentState;
};
```

## Performance Optimizations

### Intelligent Caching
```typescript
// ANNOTATION: Advanced caching system with intelligent eviction policies
// Uses access patterns, temporal data, and user behavior to optimize cache performance
// Implements smart eviction algorithms to maintain optimal memory usage
class IntelligentCacheManager {
  private cache = new Map<string, CachedRoomData>();
  private accessPatterns = new Map<string, AccessPattern>();
  private readonly maxCacheSize = 100; // rooms
  private readonly baseEvictionTime = 30 * 60 * 1000; // 30 minutes
  
  // Cache with smart eviction
  async cacheRoomData(roomId: string, data: RoomData): Promise<void> {
    // Update access pattern
    this.updateAccessPattern(roomId);
    
    // Check cache size and evict if necessary
    if (this.cache.size >= this.maxCacheSize) {
      await this.intelligentEviction();
    }
    
    // Store with metadata
    this.cache.set(roomId, {
      data,
      timestamp: Date.now(),
      accessCount: this.accessPatterns.get(roomId)?.count || 0,
      priority: this.calculateCachePriority(roomId)
    });
  }
  
  // Smart eviction based on usage patterns
  private async intelligentEviction(): Promise<void> {
    const entries = Array.from(this.cache.entries());
    
    // Score each entry for eviction
    const scored = entries.map(([roomId, cached]) => ({
      roomId,
      cached,
      evictionScore: this.calculateEvictionScore(roomId, cached)
    }));
    
    // Sort by eviction score (higher = more likely to evict)
    scored.sort((a, b) => b.evictionScore - a.evictionScore);
    
    // Evict bottom 20%
    const evictionCount = Math.ceil(entries.length * 0.2);
    for (let i = 0; i < evictionCount; i++) {
      this.cache.delete(scored[i].roomId);
      this.accessPatterns.delete(scored[i].roomId);
    }
  }
  
  // Calculate eviction score based on multiple factors
  private calculateEvictionScore(roomId: string, cached: CachedRoomData): number {
    const age = Date.now() - cached.timestamp;
    const accessPattern = this.accessPatterns.get(roomId);
    
    // Factors influencing eviction (higher score = more likely to evict)
    const ageScore = age / this.baseEvictionTime; // 0-1+ (older = higher)
    const accessScore = 1 / (1 + (accessPattern?.count || 0)); // 0-1 (less accessed = higher)
    const recencyScore = accessPattern?.lastAccess 
      ? (Date.now() - accessPattern.lastAccess) / this.baseEvictionTime 
      : 1; // 0-1+ (less recent = higher)
    const priorityScore = 1 - (cached.priority / 10); // 0-1 (lower priority = higher)
    
    return (ageScore * 0.3) + (accessScore * 0.3) + (recencyScore * 0.3) + (priorityScore * 0.1);
  }
}
```

### State Compression
```rust
// Efficient state serialization for storage
#[derive(Debug, Serialize, Deserialize)]
pub struct CompressedRoomState {
    room_id: RoomId,
    basic_info: CompactRoomInfo,
    message_digest: MessageDigest,      // Compressed message summary
    user_summary: UserSummary,          // Essential user data only
    config_hash: u64,                   // Config fingerprint
    compression_level: CompressionLevel,
    original_size: usize,
    compressed_size: usize,
}

impl CompressedRoomState {
    // Compress full room state for storage
    pub fn compress(full_state: &FullRoomState) -> Result<Self, CompressionError> {
        let message_digest = MessageDigest::from_messages(&full_state.messages)?;
        let user_summary = UserSummary::from_users(&full_state.users)?;
        let config_hash = calculate_config_hash(&full_state.room_config);
        
        let compressed = Self {
            room_id: full_state.room_id.clone(),
            basic_info: CompactRoomInfo::from(&full_state.basic_info),
            message_digest,
            user_summary,
            config_hash,
            compression_level: CompressionLevel::High,
            original_size: full_state.estimated_size(),
            compressed_size: 0, // Will be updated after serialization
        };
        
        Ok(compressed)
    }
    
    // Decompress for use (partial restoration)
    pub async fn decompress(&self) -> Result<PartialRoomState, CompressionError> {
        // Restore basic state
        let basic_state = PartialRoomState {
            room_id: self.room_id.clone(),
            basic_info: self.basic_info.expand(),
            recent_activity: self.message_digest.extract_activity_summary(),
            user_count: self.user_summary.total_count,
            last_update: self.message_digest.last_message_time,
        };
        
        Ok(basic_state)
    }
}

// Message digest for efficient storage
#[derive(Debug, Serialize, Deserialize)]
pub struct MessageDigest {
    message_count: u32,
    last_message_time: DateTime<Utc>,
    user_activity_summary: HashMap<UserId, u32>, // user -> message count
    keyword_frequency: HashMap<String, u32>,      // popular terms
    emote_usage: HashMap<EmoteId, u32>,          // emote popularity
    digest_version: u8,
}
```

## Conflict Resolution

### State Synchronization Conflicts
```rust
// Handle simultaneous state updates
pub enum ConflictResolution {
    ServerWins,           // Server state takes precedence
    ClientWins,           // Client state preserved
    Merge,                // Intelligent merge of states
    UserChoice,           // Prompt user for resolution
}

impl RoomStateManager {
    // Resolve state conflicts when client and server diverge
    pub async fn resolve_state_conflict(&mut self,
        room_id: &RoomId,
        client_state: &RoomState,
        server_state: &RoomState,
        conflict_type: ConflictType
    ) -> Result<RoomState, ConflictError> {
        
        match conflict_type {
            ConflictType::MessageOrder => {
                // Merge message lists by timestamp
                self.merge_message_timelines(client_state, server_state)
            },
            
            ConflictType::UserPresence => {
                // Server user list is authoritative
                let mut resolved = server_state.clone();
                resolved.messages = client_state.messages.clone();
                Ok(resolved)
            },
            
            ConflictType::RoomConfig => {
                // Config changes always come from server
                let mut resolved = client_state.clone();
                resolved.room_config = server_state.room_config.clone();
                Ok(resolved)
            },
            
            ConflictType::ComplexMerge => {
                // Requires intelligent merging
                self.intelligent_state_merge(client_state, server_state).await
            }
        }
    }
    
    // Intelligent merge algorithm
    async fn intelligent_state_merge(&self,
        client_state: &RoomState,
        server_state: &RoomState
    ) -> Result<RoomState, ConflictError> {
        
        let mut merged = server_state.clone(); // Start with server as base
        
        // Merge messages by timestamp, removing duplicates
        let mut all_messages = Vec::new();
        all_messages.extend(client_state.messages.iter().cloned());
        all_messages.extend(server_state.messages.iter().cloned());
        
        // Deduplicate and sort by timestamp
        all_messages.sort_by(|a, b| a.timestamp.cmp(&b.timestamp));
        all_messages.dedup_by(|a, b| a.id == b.id);
        
        // Keep only recent messages to prevent unbounded growth
        if all_messages.len() > 1000 {
            all_messages = all_messages.into_iter().rev().take(1000).rev().collect();
        }
        
        merged.messages = all_messages;
        
        // Merge user states (server wins for presence, client wins for UI state)
        for (user_id, client_user) in &client_state.users {
            if let Some(server_user) = server_state.users.get(user_id) {
                // Merge user state
                let merged_user = UserState {
                    id: server_user.id.clone(),
                    presence: server_user.presence.clone(),  // Server authoritative
                    badges: server_user.badges.clone(),      // Server authoritative
                    ui_state: client_user.ui_state.clone(),  // Client preserved
                    ..server_user.clone()
                };
                merged.users.insert(user_id.clone(), merged_user);
            }
        }
        
        Ok(merged)
    }
}
```

## Migration Strategy

### Phase 1: Core State Management (Weeks 1-4)
- [ ] **State Level Architecture**: Implement active/background/cached state hierarchy
- [ ] **Basic Synchronization**: Real-time state sync for active rooms
- [ ] **Simple Caching**: LRU cache for recently visited rooms
- [ ] **State Transitions**: Basic promote/demote operations

### Phase 2: Advanced Features (Weeks 5-8)
- [ ] **Intelligent Caching**: Smart eviction and predictive warming
- [ ] **Conflict Resolution**: Handle concurrent state updates
- [ ] **State Compression**: Efficient storage and transmission
- [ ] **Performance Optimization**: Memory and network optimizations

### Phase 3: Production Hardening (Weeks 9-12)
- [ ] **Monitoring & Metrics**: State management observability
- [ ] **Error Handling**: Robust error recovery and fallbacks
- [ ] **Load Testing**: Performance validation under high load
- [ ] **Cross-Platform Integration**: Ensure consistent behavior across platforms

## Success Metrics

### Performance Targets
- **State Transition Speed**: <100ms for promote/demote operations
- **Memory Efficiency**: <10MB per background room state
- **Cache Hit Rate**: >90% for frequently accessed rooms
- **Sync Latency**: <50ms for state update propagation

### Reliability Targets
- **State Consistency**: >99.9% consistency across clients
- **Conflict Resolution**: <0.01% unresolved conflicts
- **Data Integrity**: Zero message loss during state transitions
- **Error Recovery**: <2 seconds for automatic error recovery

## Related Components

- **[[chatroom-navigation]]** - Main navigation architecture document
- **[[../Backend/chat]]** - Backend chat service integration
- **[[../../../../RUST CONVERSION/Components/Chat-Service]]** - Rust migration target
- **[[../Performance/chat-caching]]** - Performance optimization strategies
- **[[../Security/chat-security]]** - Security considerations for state management

---

*This room state management architecture enables efficient, consistent, and performant multi-room chat experiences through intelligent state synchronization, caching, and conflict resolution mechanisms.*
