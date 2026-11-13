import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  Button,
  CircularProgress,
  LinearProgress,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider
} from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import axios from 'axios';
import API_BASE_URL from '../config';

const TYPE_COLORS = {
  numeric: 'primary',
  categorical: 'secondary',
  text: 'default',
  datetime: 'info',
  boolean: 'warning',
  empty: 'error'
};

const TYPE_ICONS = {
  numeric: '🔢',
  categorical: '🏷️',
  text: '📝',
  datetime: '📅',
  boolean: '✅',
  empty: '❌'
};

const fmt = (v) => {
  if (v === null || v === undefined) return '–';
  if (typeof v !== 'number') return String(v);
  if (!Number.isFinite(v)) return '–';
  if (Number.isInteger(v)) return v.toLocaleString();
  return v.toLocaleString(undefined, { maximumFractionDigits: 3 });
};

const fmtPct = (v) => (v === null || v === undefined ? '–' : `${fmt(Math.round(v * 10) / 10)}%`);

const fmtBytes = (b) => {
  if (b === null || b === undefined) return '–';
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
};

const STAT_ORDER = [
  'mean', 'std', 'min', 'q1', 'median', 'q3', 'max', 'skew', 'zeros', 'outliers',
  'min_length', 'max_length', 'avg_length', 'range_days'
];

const StatCard = ({ label, value, sub }) => (
  <Card variant="outlined" sx={{ height: '100%' }}>
    <CardContent sx={{ '&:last-child': { pb: 2 } }}>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="h6" sx={{ lineHeight: 1.2 }}>{value}</Typography>
      {sub && <Typography variant="caption" color="text.secondary">{sub}</Typography>}
    </CardContent>
  </Card>
);

const Histogram = ({ histogram }) => {
  const counts = histogram?.counts || [];
  const edges = histogram?.edges || [];
  if (counts.length === 0) return null;
  const maxCount = Math.max(...counts, 1);
  const H = 60;
  const W = 100;
  const barW = W / counts.length;
  const label = (e) => (typeof e === 'number' ? fmt(e) : String(e ?? ''));
  return (
    <Box sx={{ mt: 1 }}>
      <Box
        component="svg"
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        sx={{ width: '100%', height: H, display: 'block', color: 'primary.main' }}
      >
        {counts.map((c, i) => {
          const h = (c / maxCount) * (H - 2);
          return (
            <rect key={i} x={i * barW + 0.3} y={H - h} width={Math.max(barW - 0.6, 0.1)} height={h} fill="currentColor" opacity={0.8}>
              <title>{`${label(edges[i])} – ${label(edges[i + 1])}: ${fmt(c)}`}</title>
            </rect>
          );
        })}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
        <Typography variant="caption" color="text.secondary" noWrap>{label(edges[0])}</Typography>
        <Typography variant="caption" color="text.secondary" noWrap>{label(edges[edges.length - 1])}</Typography>
      </Box>
    </Box>
  );
};

const StatsGrid = ({ stats }) => {
  const keys = [
    ...STAT_ORDER.filter((k) => k in stats),
    ...Object.keys(stats).filter((k) => !STAT_ORDER.includes(k))
  ];
  if (keys.length === 0) return null;
  return (
    <Grid container spacing={0.5} sx={{ mt: 1 }}>
      {keys.map((k) => (
        <Grid item xs={6} sm={4} key={k}>
          <Typography variant="caption" color="text.secondary" component="div" noWrap>
            {k.replace(/_/g, ' ')}
          </Typography>
          <Typography variant="body2" noWrap title={fmt(stats[k])}>{fmt(stats[k])}</Typography>
        </Grid>
      ))}
    </Grid>
  );
};

const TopValues = ({ values }) => (
  <Box sx={{ mt: 1 }}>
    {values.slice(0, 5).map((tv, i) => (
      <Box key={i} sx={{ mb: 0.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
          <Typography variant="caption" noWrap title={String(tv.value)} sx={{ minWidth: 0 }}>
            {String(tv.value)}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
            {fmt(tv.count)} ({fmtPct(tv.pct)})
          </Typography>
        </Box>
        <Box sx={{ height: 6, borderRadius: 1, bgcolor: 'action.hover' }}>
          <Box sx={{ height: '100%', borderRadius: 1, bgcolor: 'secondary.main', width: `${Math.min(Math.max(tv.pct || 0, 0), 100)}%` }} />
        </Box>
      </Box>
    ))}
  </Box>
);

const ColumnCard = ({ col }) => (
  <Card variant="outlined" sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, mb: 1 }}>
        <Typography variant="subtitle1" noWrap title={col.name} sx={{ minWidth: 0, fontWeight: 500 }}>
          {col.name}
        </Typography>
        <Chip
          size="small"
          label={`${TYPE_ICONS[col.type] || '❓'} ${col.type}`}
          color={TYPE_COLORS[col.type] || 'default'}
          sx={{ flexShrink: 0 }}
        />
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(Math.max(col.missing_pct || 0, 0), 100)}
        color={(col.missing_pct || 0) > 20 ? 'warning' : 'primary'}
        sx={{ height: 6, borderRadius: 1 }}
      />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {fmt(col.missing)} missing ({fmtPct(col.missing_pct)})
        </Typography>
        <Typography variant="caption" color="text.secondary">{fmt(col.unique)} unique</Typography>
      </Box>
      {col.histogram && <Histogram histogram={col.histogram} />}
      {col.stats && <StatsGrid stats={col.stats} />}
      {col.top_values && col.top_values.length > 0 && <TopValues values={col.top_values} />}
    </CardContent>
  </Card>
);

const DataProfile = ({ refreshKey, onError }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');

  // Keep the latest onError without retriggering the loader on parent re-renders
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/profile`);
      setProfile(response.data);
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to load data profile';
      setError(message);
      onErrorRef.current?.(message);
      console.error('Error loading data profile:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile, refreshKey]);

  const columns = useMemo(() => profile?.columns || [], [profile]);
  const typesPresent = useMemo(() => [...new Set(columns.map((c) => c.type))], [columns]);
  const visibleColumns = useMemo(() => {
    const q = search.trim().toLowerCase();
    return columns.filter(
      (c) =>
        (typeFilter === 'all' || c.type === typeFilter) &&
        (!q || String(c.name).toLowerCase().includes(q))
    );
  }, [columns, search, typeFilter]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !profile) {
    return (
      <Alert severity="error" action={<Button color="inherit" size="small" onClick={loadProfile}>Retry</Button>}>
        {error || 'Failed to load data profile'}
      </Alert>
    );
  }

  const ov = profile.overview || {};
  const alerts = [...(profile.alerts || [])].sort(
    (a, b) => (a.severity === 'warning' ? 0 : 1) - (b.severity === 'warning' ? 0 : 1)
  );
  const correlations = profile.correlations || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        <Typography variant="h5">Data Profile</Typography>
        {ov.has_filters && (
          <Chip color="info" size="small" label={`Filtered: ${fmt(ov.rows)} of ${fmt(ov.total_rows)} rows`} />
        )}
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={2}><StatCard label="Rows" value={fmt(ov.rows)} /></Grid>
        <Grid item xs={6} md={2}><StatCard label="Columns" value={fmt(ov.columns)} /></Grid>
        <Grid item xs={6} md={2}>
          <StatCard label="Missing cells" value={fmt(ov.missing_cells)} sub={fmtPct(ov.missing_pct)} />
        </Grid>
        <Grid item xs={6} md={2}><StatCard label="Duplicate rows" value={fmt(ov.duplicate_rows)} /></Grid>
        <Grid item xs={6} md={2}><StatCard label="Memory" value={fmtBytes(ov.memory_bytes)} /></Grid>
        <Grid item xs={6} md={2}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent sx={{ '&:last-child': { pb: 2 } }}>
              <Typography variant="caption" color="text.secondary" component="div">Column types</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                {Object.entries(ov.type_counts || {}).map(([t, n]) => (
                  <Chip key={t} size="small" color={TYPE_COLORS[t] || 'default'} label={`${TYPE_ICONS[t] || '❓'} ${n}`} title={t} />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>Data quality alerts</Typography>
      {alerts.length === 0 ? (
        <Alert severity="success" sx={{ mb: 3 }}>No data quality issues detected</Alert>
      ) : (
        <Box sx={{ mb: 3 }}>
          {alerts.map((a, i) => (
            <Box key={i} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, py: 0.5 }}>
              {a.severity === 'warning' ? (
                <WarningAmberIcon fontSize="small" sx={{ color: 'warning.main', mt: '2px' }} />
              ) : (
                <InfoOutlinedIcon fontSize="small" sx={{ color: 'info.main', mt: '2px' }} />
              )}
              <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>{a.message}</Typography>
            </Box>
          ))}
        </Box>
      )}

      {correlations.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Strongest correlations</Typography>
          {correlations.map((c, i) => (
            <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 0.5 }}>
              <Typography variant="body2" noWrap title={`${c.a} ↔ ${c.b}`} sx={{ flex: '1 1 40%', minWidth: 0 }}>
                {c.a} ↔ {c.b}
              </Typography>
              <Typography variant="body2" sx={{ width: 48, textAlign: 'right' }}>
                {typeof c.r === 'number' ? c.r.toFixed(2) : '–'}
              </Typography>
              <Box sx={{ flex: '1 1 40%', height: 8, borderRadius: 1, bgcolor: 'action.hover' }}>
                <Box
                  sx={{
                    height: '100%',
                    borderRadius: 1,
                    width: `${Math.min(Math.abs(c.r || 0), 1) * 100}%`,
                    bgcolor: (c.r || 0) >= 0 ? 'primary.main' : 'error.main'
                  }}
                />
              </Box>
            </Box>
          ))}
        </Box>
      )}

      <Divider sx={{ mb: 2 }} />
      <Typography variant="h6" gutterBottom>Columns</Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={8}>
          <TextField
            size="small"
            fullWidth
            label="Search columns"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <FormControl size="small" fullWidth>
            <InputLabel id="profile-type-filter-label">Type</InputLabel>
            <Select
              labelId="profile-type-filter-label"
              label="Type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              {typesPresent.map((t) => (
                <MenuItem key={t} value={t}>{`${TYPE_ICONS[t] || '❓'} ${t}`}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {visibleColumns.length === 0 ? (
        <Typography color="text.secondary">No columns match.</Typography>
      ) : (
        <Grid container spacing={2}>
          {visibleColumns.map((col) => (
            <Grid item xs={12} md={6} key={col.name}>
              <ColumnCard col={col} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default DataProfile;
