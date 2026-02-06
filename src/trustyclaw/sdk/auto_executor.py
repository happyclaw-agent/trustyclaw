"""
Auto-Execution Engine for TrustyClaw

Purpose:
    Monitors mandate deadlines and automatically executes actions.
    
Capabilities:
    - Monitor mandate deadlines
    - Auto-complete when deliverable hash matches
    - Auto-release funds after acceptance window
    - Auto-escalate disputes
    
Usage:
    >>> engine = AutoExecutor()
    >>> engine.start()
    >>> # Engine monitors and auto-executes in background
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional
import threading
import time
import hashlib
import json


class ExecutionEvent(Enum):
    """Types of auto-execution events"""
    DEADLINE_WARNING = "deadline_warning"
    DEADLINE_EXPIRED = "deadline_expired"
    DELIVERABLE_SUBMITTED = "deliverable_submitted"
    DELIVERABLE_VERIFIED = "deliverable_verified"
    FUNDS_RELEASED = "funds_released"
    FUNDS_REFUNDED = "funds_refunded"
    DISPUTE_ESCALATED = "dispute_escalated"
    MANDATE_COMPLETED = "mandate_completed"


@dataclass
class ExecutionContext:
    """
    Context for auto-execution actions.
    
    Contains all information needed to make execution decisions.
    """
    mandate_id: str
    provider: str
    renter: str
    amount: int
    deadline: str
    deliverable_hash: Optional[str] = None
    expected_hash: Optional[str] = None
    escrow_id: Optional[str] = None
    dispute_count: int = 0
    events: List[ExecutionEvent] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "mandate_id": self.mandate_id,
            "provider": self.provider,
            "renter": self.renter,
            "amount": self.amount,
            "deadline": self.deadline,
            "deliverable_hash": self.deliverable_hash,
            "expected_hash": self.expected_hash,
            "escrow_id": self.escrow_id,
            "dispute_count": self.dispute_count,
            "events": [e.value for e in self.events],
            "metadata": self.metadata,
        }


@dataclass
class ExecutionResult:
    """
    Result of an auto-execution action.
    
    Contains success status, details, and any errors.
    """
    success: bool
    event: ExecutionEvent
    message: str
    details: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "event": self.event.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class ExecutionRule:
    """
    Rule for automatic execution.
    
    Defines conditions and actions for automation.
    
    Attributes:
        rule_id: Unique rule identifier
        name: Human-readable name
        event: Event that triggers the rule
        condition: Callable that returns bool
        action: Callable to execute
        enabled: Whether rule is active
        priority: Execution priority (lower = higher priority)
    """
    rule_id: str
    name: str
    event: ExecutionEvent
    condition: Callable[[ExecutionContext], bool]
    action: Callable[[ExecutionContext], ExecutionResult]
    enabled: bool = True
    priority: int = 100
    executions_count: int = 0
    last_executed: Optional[str] = None


class AutoExecutor:
    """
    Engine for automatic mandate execution.
    
    Features:
    - Deadline monitoring
    - Automatic deliverable verification
    - Auto-fund release after acceptance window
    - Auto-dispute escalation
    - Extensible rule system
    
    Usage:
        >>> executor = AutoExecutor()
        >>> 
        >>> # Add custom rule
        >>> executor.add_rule(ExecutionRule(
        ...     name="Auto-complete",
        ...     event=ExecutionEvent.DELIVERABLE_SUBMITTED,
        ...     condition=lambda ctx: ctx.expected_hash == ctx.deliverable_hash,
        ...     action=lambda ctx: ExecutionResult(True, ...),
        ... ))
        >>> 
        >>> # Start monitoring
        >>> executor.start()
    """
    
    DEADLINE_WARNING_HOURS = 4
    ACCEPTANCE_WINDOW_HOURS = 24
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize auto-executor.
        
        Args:
            check_interval: Seconds between deadline checks
        """
        self.check_interval = check_interval
        self._running = False
        self._monitor_thread = None
        self._rules: List[ExecutionRule] = []
        self._execution_history: List[ExecutionResult] = []
        self._callbacks: Dict[ExecutionEvent, List[Callable]] = {}
        
        # Initialize default rules
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize built-in execution rules"""
        
        # Rule: Auto-complete when deliverable hash matches
        self.add_rule(ExecutionRule(
            rule_id="auto-complete-hash",
            name="Auto-complete on hash match",
            event=ExecutionEvent.DELIVERABLE_SUBMITTED,
            condition=lambda ctx: (
                ctx.expected_hash is not None and
                ctx.deliverable_hash is not None and
                ctx.expected_hash == ctx.deliverable_hash
            ),
            action=self._auto_complete_action,
            priority=10,
        ))
        
        # Rule: Auto-release funds after acceptance window
        self.add_rule(ExecutionRule(
            rule_id="auto-release-funds",
            name="Auto-release funds after window",
            event=ExecutionEvent.MANDATE_COMPLETED,
            condition=lambda ctx: True,  # Always execute
            action=self._auto_release_action,
            priority=20,
        ))
        
        # Rule: Auto-escalate disputes at threshold
        self.add_rule(ExecutionRule(
            rule_id="auto-escalate-dispute",
            name="Escalate disputes at threshold",
            event=ExecutionEvent.DISPUTE_ESCALATED,
            condition=lambda ctx: ctx.dispute_count >= 3,
            action=self._escalate_dispute_action,
            priority=5,
        ))
        
        # Rule: Warn before deadline
        self.add_rule(ExecutionRule(
            rule_id="deadline-warning",
            name="Warn before deadline expires",
            event=ExecutionEvent.DEADLINE_WARNING,
            condition=lambda ctx: True,
            action=self._deadline_warning_action,
            priority=50,
        ))
    
    def start(self):
        """Start the auto-executor background monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        print(f"AutoExecutor started (check interval: {self.check_interval}s)")
    
    def stop(self):
        """Stop the auto-executor"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        print("AutoExecutor stopped")
    
    def add_rule(self, rule: ExecutionRule):
        """Add a custom execution rule"""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
        print(f"Added rule: {rule.name} (priority: {rule.priority})")
    
    def remove_rule(self, rule_id: str):
        """Remove a rule by ID"""
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
    
    def register_callback(
        self,
        event: ExecutionEvent,
        callback: Callable[[ExecutionContext, ExecutionResult], None],
    ):
        """Register callback for execution events"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def trigger_event(
        self,
        event: ExecutionEvent,
        context: ExecutionContext,
    ) -> List[ExecutionResult]:
        """
        Trigger an event and execute matching rules.
        
        Args:
            event: Event to trigger
            context: Execution context
            
        Returns:
            List of execution results
        """
        results = []
        context.events.append(event)
        
        for rule in self._rules:
            if not rule.enabled:
                continue
            if rule.event != event:
                continue
            
            try:
                if rule.condition(context):
                    result = rule.action(context)
                    result.event = event
                    results.append(result)
                    
                    # Update rule stats
                    rule.executions_count += 1
                    rule.last_executed = datetime.utcnow().isoformat()
                    
                    # Call callbacks
                    self._call_event_callbacks(event, context, result)
                    
                    # Record in history
                    self._execution_history.append(result)
            except Exception as e:
                error_result = ExecutionResult(
                    success=False,
                    event=event,
                    message=f"Rule {rule.rule_id} failed: {str(e)}",
                    details={"error": str(e), "rule_id": rule.rule_id},
                )
                results.append(error_result)
                self._execution_history.append(error_result)
        
        return results
    
    def _call_event_callbacks(
        self,
        event: ExecutionEvent,
        context: ExecutionContext,
        result: ExecutionResult,
    ):
        """Call registered callbacks for an event"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(context, result)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    def _monitor_loop(self):
        """Background loop for deadline monitoring"""
        while self._running:
            try:
                self._check_deadlines()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Monitor loop error: {e}")
                time.sleep(self.check_interval)
    
    def _check_deadlines(self):
        """Check all active mandates for deadline issues"""
        # This would query the mandate storage
        # For now, just a placeholder
        pass
    
    # ============ Built-in Actions ============
    
    def _auto_complete_action(self, context: ExecutionContext) -> ExecutionResult:
        """Action: Auto-complete mandate when hash matches"""
        return ExecutionResult(
            success=True,
            event=ExecutionEvent.DELIVERABLE_VERIFIED,
            message=f"Auto-completed mandate {context.mandate_id}",
            details={
                "deliverable_hash": context.deliverable_hash,
                "action": "complete",
            },
        )
    
    def _auto_release_action(self, context: ExecutionContext) -> ExecutionResult:
        """Action: Auto-release funds to provider"""
        return ExecutionResult(
            success=True,
            event=ExecutionEvent.FUNDS_RELEASED,
            message=f"Released {context.amount} to provider",
            details={
                "amount": context.amount,
                "recipient": context.provider,
                "escrow_id": context.escrow_id,
            },
        )
    
    def _escalate_dispute_action(self, context: ExecutionContext) -> ExecutionResult:
        """Action: Escalate dispute to community"""
        return ExecutionResult(
            success=True,
            event=ExecutionEvent.DISPUTE_ESCALATED,
            message=f"Escalated dispute for {context.mandate_id} to community voting",
            details={
                "dispute_count": context.dispute_count,
                "action": "escalate",
            },
        )
    
    def _deadline_warning_action(self, context: ExecutionContext) -> ExecutionResult:
        """Action: Send deadline warning"""
        return ExecutionResult(
            success=True,
            event=ExecutionEvent.DEADLINE_WARNING,
            message=f"Deadline warning for {context.mandate_id}",
            details={
                "deadline": context.deadline,
                "action": "warn",
            },
        )
    
    # ============ Helper Methods ============
    
    def verify_deliverable_hash(
        self,
        deliverable_content: str,
        expected_hash: str,
    ) -> bool:
        """
        Verify deliverable content against expected hash.
        
        Args:
            deliverable_content: Raw deliverable content
            expected_hash: Expected SHA256 hash
            
        Returns:
            True if hash matches
        """
        actual_hash = hashlib.sha256(deliverable_content.encode()).hexdigest()
        return actual_hash == expected_hash
    
    def calculate_deliverable_hash(self, content: str) -> str:
        """
        Calculate SHA256 hash of deliverable content.
        
        Args:
            content: Raw deliverable content
            
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def is_deadline_expired(self, deadline: str) -> bool:
        """Check if deadline has passed"""
        return datetime.utcnow() > datetime.fromisoformat(deadline)
    
    def get_deadline_status(self, deadline: str) -> str:
        """Get human-readable deadline status"""
        deadline_dt = datetime.fromisoformat(deadline)
        now = datetime.utcnow()
        
        if now > deadline_dt:
            return "expired"
        
        remaining = deadline_dt - now
        hours = remaining.total_seconds() / 3600
        
        if hours < 1:
            return f"{int(remaining.total_seconds() / 60)} minutes"
        elif hours < 24:
            return f"{int(hours)} hours"
        else:
            return f"{int(hours / 24)} days"
    
    def create_context(
        self,
        mandate_id: str,
        provider: str,
        renter: str,
        amount: int,
        deadline: str,
        escrow_id: str = None,
        expected_hash: str = None,
        dispute_count: int = 0,
    ) -> ExecutionContext:
        """Create an execution context"""
        return ExecutionContext(
            mandate_id=mandate_id,
            provider=provider,
            renter=renter,
            amount=amount,
            deadline=deadline,
            escrow_id=escrow_id,
            expected_hash=expected_hash,
            dispute_count=dispute_count,
        )
    
    def get_execution_history(
        self,
        mandate_id: str = None,
        event: ExecutionEvent = None,
    ) -> List[ExecutionResult]:
        """Get execution history with optional filters"""
        history = self._execution_history
        
        if mandate_id:
            history = [r for r in history if mandate_id in r.message]
        
        if event:
            history = [r for r in history if r.event == event]
        
        return history
    
    def get_stats(self) -> dict:
        """Get executor statistics"""
        return {
            "total_executions": len(self._execution_history),
            "successful": sum(1 for r in self._execution_history if r.success),
            "failed": sum(1 for r in self._execution_history if not r.success),
            "active_rules": sum(1 for r in self._rules if r.enabled),
            "total_rules": len(self._rules),
            "is_running": self._running,
        }


# ============ Factory Functions ============

def get_auto_executor(check_interval: int = 60) -> AutoExecutor:
    """
    Get an AutoExecutor instance.
    
    Args:
        check_interval: Seconds between checks
        
    Returns:
        Configured AutoExecutor
    """
    return AutoExecutor(check_interval=check_interval)


# ============ CLI Demo ============

def demo():
    """Demo the auto-execution engine"""
    executor = AutoExecutor(check_interval=10)
    
    # Register callback
    def on_complete(context, result):
        print(f"   [Callback] {result.message}")
    
    executor.register_callback(ExecutionEvent.FUNDS_RELEASED, on_complete)
    
    # Create context
    context = executor.create_context(
        mandate_id="mandate-demo-1",
        provider="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
        renter="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
        amount=1000000,
        deadline=(datetime.utcnow() + timedelta(hours=24)).isoformat(),
        expected_hash="abc123def456",
    )
    
    # Simulate deliverable submission
    context.deliverable_hash = "abc123def456"
    
    print("1. Triggering deliverable event...")
    results = executor.trigger_event(ExecutionEvent.DELIVERABLE_SUBMITTED, context)
    for result in results:
        print(f"   Result: {result.message}")
    
    # Check stats
    print("\n2. Executor stats:")
    stats = executor.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Show deadline status
    print(f"\n3. Deadline status: {executor.get_deadline_status(context.deadline)}")
    
    # Stop
    executor.stop()


if __name__ == "__main__":
    demo()
