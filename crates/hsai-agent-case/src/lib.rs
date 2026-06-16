#![forbid(unsafe_code)]
//! The agent case: the observation context an evidence lane assesses against.
//!
//! A [`Case`] fixes *when* a lane verifies ([`Case::observed_at`]) and *which*
//! time windows the observer is willing to accept ([`Case::accepted_windows`]).
//! A lane uses `observed_at` as its verification time and intersects the case's
//! accepted windows with any windows the lane itself enforces.
//!
//! Time is a plain monotonic `u64` tick. [`TimeWindow`] is half-open
//! `[start, end)`: `start` is included, `end` is excluded.

/// A half-open time window `[start, end)`.
///
/// A window is only constructed when it is non-empty (`start < end`). An empty
/// window has no valid representation; [`TimeWindow::new`] returns `None` for
/// `start >= end`, and [`TimeWindow::intersect`] returns `None` when the overlap
/// is empty.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct TimeWindow {
    start: u64,
    end: u64,
}

impl TimeWindow {
    /// Construct a non-empty window `[start, end)`. Returns `None` if
    /// `start >= end`.
    pub fn new(start: u64, end: u64) -> Option<Self> {
        if start < end {
            Some(Self { start, end })
        } else {
            None
        }
    }

    /// Inclusive lower bound.
    pub fn start(&self) -> u64 {
        self.start
    }

    /// Exclusive upper bound.
    pub fn end(&self) -> u64 {
        self.end
    }

    /// True when `t` lies in `[start, end)`.
    pub fn contains(&self, t: u64) -> bool {
        self.start <= t && t < self.end
    }

    /// Intersect two windows. Returns `None` when the overlap is empty.
    pub fn intersect(&self, other: &TimeWindow) -> Option<TimeWindow> {
        TimeWindow::new(self.start.max(other.start), self.end.min(other.end))
    }
}

/// The observation context an evidence lane assesses against.
///
/// `observed_at` is the verification time the lane must use. `accepted_windows`
/// are the time windows the observer accepts; a lane intersects them with its
/// own windows to decide whether the observation is admissible.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Case {
    case_id: String,
    observed_at: u64,
    accepted_windows: Vec<TimeWindow>,
}

impl Case {
    /// Construct a case observed at `observed_at` accepting `accepted_windows`.
    pub fn new(
        case_id: impl Into<String>,
        observed_at: u64,
        accepted_windows: Vec<TimeWindow>,
    ) -> Self {
        Self {
            case_id: case_id.into(),
            observed_at,
            accepted_windows,
        }
    }

    /// Construct a case with no observer-side window restriction.
    pub fn at(case_id: impl Into<String>, observed_at: u64) -> Self {
        Self::new(case_id, observed_at, Vec::new())
    }

    /// Stable identity of the case.
    pub fn case_id(&self) -> &str {
        &self.case_id
    }

    /// The verification time a lane must use.
    pub fn observed_at(&self) -> u64 {
        self.observed_at
    }

    /// The windows the observer accepts. A lane intersects these with its own.
    pub fn accepted_windows(&self) -> &[TimeWindow] {
        &self.accepted_windows
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_window_has_no_representation() {
        assert!(TimeWindow::new(5, 5).is_none());
        assert!(TimeWindow::new(6, 5).is_none());
        assert!(TimeWindow::new(4, 5).is_some());
    }

    #[test]
    fn intersect_is_overlap() {
        let a = TimeWindow::new(0, 10).unwrap();
        let b = TimeWindow::new(5, 20).unwrap();
        assert_eq!(a.intersect(&b), TimeWindow::new(5, 10));
        let c = TimeWindow::new(20, 30).unwrap();
        assert!(a.intersect(&c).is_none());
    }

    #[test]
    fn half_open_contains() {
        let w = TimeWindow::new(5, 10).unwrap();
        assert!(w.contains(5));
        assert!(w.contains(9));
        assert!(!w.contains(10));
        assert!(!w.contains(4));
    }

    #[test]
    fn case_exposes_observed_at() {
        let c = Case::at("c1", 42);
        assert_eq!(c.observed_at(), 42);
        assert!(c.accepted_windows().is_empty());
    }
}
