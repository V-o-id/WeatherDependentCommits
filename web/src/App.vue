<script setup lang="ts">
import { computed, ref } from "vue";

type CityResult = {
  label: string;
  latitude: number;
  longitude: number;
};

type EnrichedRow = {
  date: string;
  month: string;
  weekday: number;
  commits: number;
  rain: number;
};

type AnalysisData = {
  rows: EnrichedRow[];
  meta: {
    owner: string;
    repo: string;
    branch: string;
    locationLabel: string;
    startDate: string;
    endDate: string;
  };
};

const repoInput = ref("V-o-id/WeatherDependentCommits");
const latitude = ref("48.303056");
const longitude = ref("14.290556");
const cityQuery = ref("");
const cityResults = ref<CityResult[]>([]);
const isCityLoading = ref(false);
const locationLabel = ref("");
const rainThreshold = ref(5);

const isLoading = ref(false);
const errorMessage = ref("");
const warnings = ref<string[]>([]);
const analysisData = ref<AnalysisData | null>(null);

const weekdayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function parseRepositoryInput(value: string) {
  const input = value.trim();
  if (!input) {
    throw new Error("Please enter a repository in owner/repo format or a GitHub URL.");
  }

  if (input.includes("github.com")) {
    const cleaned = input.replace(/\.git$/, "").replace(/\/+$/, "");
    const parts = cleaned.split("/");
    const repo = parts[parts.length - 1];
    const owner = parts[parts.length - 2];
    if (!owner || !repo) {
      throw new Error("Could not parse repository URL.");
    }
    return { owner, repo };
  }

  const segments = input.split("/").map((segment) => segment.trim());
  if (segments.length !== 2 || !segments[0] || !segments[1]) {
    throw new Error("Use owner/repo format, for example: vuejs/core");
  }

  return { owner: segments[0], repo: segments[1].replace(/\.git$/, "") };
}

async function fetchJson(url: string) {
  const response = await fetch(url, {
    headers: {
      Accept: "application/vnd.github+json",
    },
  });

  if (!response.ok) {
    const fallback = `Request failed (${response.status})`;
    let detail = fallback;
    try {
      const data = await response.json();
      detail = data.message || fallback;
    } catch (_) {
      detail = fallback;
    }
    throw new Error(detail);
  }

  return response.json();
}

async function fetchCommitDates(owner: string, repo: string, branch: string) {
  const commitDates = [];
  const perPage = 100;
  const maxPages = 30;

  for (let page = 1; page <= maxPages; page += 1) {
    const pageUrl = `https://api.github.com/repos/${owner}/${repo}/commits?sha=${branch}&per_page=${perPage}&page=${page}`;
    const pageData = await fetchJson(pageUrl);

    if (!Array.isArray(pageData) || pageData.length === 0) {
      break;
    }

    for (const commit of pageData) {
      const timestamp = commit?.commit?.author?.date;
      if (timestamp) {
        commitDates.push(timestamp.slice(0, 10));
      }
    }

    if (pageData.length < perPage) {
      break;
    }

    if (page === maxPages) {
      warnings.value.push("Only the latest 3000 commits are included in this analysis.");
    }
  }

  if (commitDates.length === 0) {
    throw new Error("No commits found on the default branch.");
  }

  return commitDates;
}

function countCommitsByDate(commitDates: string[]) {
  const map = new Map();
  for (const day of commitDates) {
    map.set(day, (map.get(day) || 0) + 1);
  }
  return map;
}

async function fetchRainByDate(lat: number, lon: number, startDate: string, endDate: string) {
  const params = new URLSearchParams({
    latitude: String(lat),
    longitude: String(lon),
    start_date: startDate,
    end_date: endDate,
    daily: "rain_sum",
    timezone: "UTC",
  });

  const url = `https://archive-api.open-meteo.com/v1/archive?${params.toString()}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Weather API failed (${response.status}).`);
  }

  const payload = await response.json();
  const times = payload?.daily?.time || [];
  const rainValues = payload?.daily?.rain_sum || [];

  const rainMap = new Map();
  for (let i = 0; i < times.length; i += 1) {
    const rain = typeof rainValues[i] === "number" ? rainValues[i] : 0;
    rainMap.set(times[i], rain);
  }

  return rainMap;
}

function formatCityResult(result: { name?: string; admin1?: string; country?: string }) {
  const parts = [result.name, result.admin1, result.country].filter(Boolean);
  return parts.join(", ");
}

async function searchCities() {
  const query = cityQuery.value.trim();
  cityResults.value = [];

  if (!query) {
    errorMessage.value = "Enter a city name to search.";
    return;
  }

  errorMessage.value = "";
  isCityLoading.value = true;

  try {
    const params = new URLSearchParams({
      name: query,
      count: "8",
      language: "en",
      format: "json",
    });

    const response = await fetch(`https://geocoding-api.open-meteo.com/v1/search?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`City search failed (${response.status}).`);
    }

    const payload = await response.json();
    const results = Array.isArray(payload?.results) ? payload.results : [];

    cityResults.value = results.map((result: { name?: string; admin1?: string; country?: string; latitude: number; longitude: number }) => ({
      label: formatCityResult(result),
      latitude: result.latitude,
      longitude: result.longitude,
    }));

    if (cityResults.value.length === 0) {
      errorMessage.value = "No matching places found.";
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Could not search cities.";
  } finally {
    isCityLoading.value = false;
  }
}

function applyCity(city: CityResult) {
  latitude.value = String(city.latitude);
  longitude.value = String(city.longitude);
  locationLabel.value = city.label;
}

function monthKey(dateString: string) {
  return dateString.slice(0, 7);
}

function getWeekday(dateString: string) {
  return new Date(`${dateString}T00:00:00Z`).getUTCDay();
}

function buildEnrichedRows(commitCountByDate: Map<string, number>, rainByDate: Map<string, number>) {
  const dates = [...commitCountByDate.keys()].sort();
  return dates.map((date) => {
    const commits = commitCountByDate.get(date) || 0;
    const rain = rainByDate.get(date) || 0;
    return {
      date,
      month: monthKey(date),
      weekday: getWeekday(date),
      commits,
      rain,
    };
  });
}

const computedStats = computed(() => {
  if (!analysisData.value) {
    return null;
  }

  const threshold = Number(rainThreshold.value);
  const rows = analysisData.value.rows;

  let rainyCommits = 0;
  let dryCommits = 0;
  let rainyDays = 0;
  let dryDays = 0;

  const monthly = new Map();
  const weekdays = new Map();

  for (const row of rows) {
    const isRainy = row.rain >= threshold;

    if (isRainy) {
      rainyCommits += row.commits;
      rainyDays += 1;
    } else {
      dryCommits += row.commits;
      dryDays += 1;
    }

    const monthData = monthly.get(row.month) || { rainy: 0, dry: 0, total: 0 };
    if (isRainy) {
      monthData.rainy += row.commits;
    } else {
      monthData.dry += row.commits;
    }
    monthData.total += row.commits;
    monthly.set(row.month, monthData);

    const weekdayData = weekdays.get(row.weekday) || { rainy: 0, dry: 0, total: 0 };
    if (isRainy) {
      weekdayData.rainy += row.commits;
    } else {
      weekdayData.dry += row.commits;
    }
    weekdayData.total += row.commits;
    weekdays.set(row.weekday, weekdayData);
  }

  const totalCommits = rainyCommits + dryCommits;
  const rainyShare = totalCommits ? (rainyCommits / totalCommits) * 100 : 0;
  const dryShare = totalCommits ? (dryCommits / totalCommits) * 100 : 0;

  const monthlyRows = [...monthly.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([month, data]) => ({ month, ...data }));

  const weekdayRows = Array.from({ length: 7 }, (_, index) => {
    const data = weekdays.get(index) || { rainy: 0, dry: 0, total: 0 };
    return {
      name: weekdayNames[index],
      ...data,
    };
  });

  const strongestDay = [...weekdayRows].sort((a, b) => b.total - a.total)[0];
  const verdict =
    rainyCommits > dryCommits
      ? "You code best when the sky is dramatic. Rainy-day productivity wins."
      : "Sunlight seems to boost your commit energy. Clear-sky coding wins.";

  return {
    threshold,
    totalCommits,
    rainyCommits,
    dryCommits,
    rainyDays,
    dryDays,
    rainyShare,
    dryShare,
    monthlyRows,
    weekdayRows,
    strongestDay,
    verdict,
    meta: analysisData.value.meta,
  };
});

async function runAnalysis() {
  errorMessage.value = "";
  warnings.value = [];
  analysisData.value = null;

  const lat = Number(latitude.value);
  const lon = Number(longitude.value);

  if (Number.isNaN(lat) || lat < -90 || lat > 90) {
    errorMessage.value = "Latitude must be a number between -90 and 90.";
    return;
  }

  if (Number.isNaN(lon) || lon < -180 || lon > 180) {
    errorMessage.value = "Longitude must be a number between -180 and 180.";
    return;
  }

  isLoading.value = true;

  try {
    const { owner, repo } = parseRepositoryInput(repoInput.value);
    const repoMeta = await fetchJson(`https://api.github.com/repos/${owner}/${repo}`);
    const branch = repoMeta.default_branch;

    const commitDates = await fetchCommitDates(owner, repo, branch);
    const commitCountByDate = countCommitsByDate(commitDates);
    const sortedDates = [...commitCountByDate.keys()].sort();

    const startDate = sortedDates[0];
    const endDate = sortedDates[sortedDates.length - 1];
    const rainByDate = await fetchRainByDate(lat, lon, startDate, endDate);

    const rows = buildEnrichedRows(commitCountByDate, rainByDate);

    analysisData.value = {
      rows,
      meta: {
        owner,
        repo,
        branch,
        locationLabel: locationLabel.value,
        startDate,
        endDate,
      },
    };
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unexpected error.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <nav class="top-nav">
      <div class="brand">WeatherDependentCommits</div>
      <div class="nav-links">
        <a href="https://github.com/V-o-id/WeatherDependentCommits" target="_blank" rel="noopener noreferrer">Repository</a>
        <a href="https://v-o-id.github.io" target="_blank" rel="noopener noreferrer">Main Site</a>
      </div>
    </nav>

    <main class="content">
      <header class="hero">
        <p class="eyebrow">Weather blaming with data</p>
        <h1>Do you commit more when it rains?</h1>
        <p>
          Analyze a public GitHub repository against historical rain data and produce a playful verdict.
        </p>
      </header>

      <section class="panel form-panel">
        <h2>Inputs</h2>
        <form class="controls" @submit.prevent="runAnalysis">
          <label>
            Repository
            <input v-model="repoInput" placeholder="owner/repo or https://github.com/owner/repo" />
          </label>
          <label>
            Latitude
            <input v-model="latitude" inputmode="decimal" placeholder="48.303056" />
          </label>
          <label>
            Longitude
            <input v-model="longitude" inputmode="decimal" placeholder="14.290556" />
          </label>

          <div class="city-picker">
            <label>
              City (optional)
              <input
                v-model="cityQuery"
                placeholder="Search city, e.g. Vienna"
                @keydown.enter.prevent="searchCities"
              />
            </label>
            <button type="button" class="city-search" :disabled="isCityLoading" @click="searchCities">
              {{ isCityLoading ? "Searching..." : "Find city" }}
            </button>
          </div>

          <div v-if="cityResults.length" class="city-results">
            <button
              v-for="city in cityResults"
              :key="`${city.label}-${city.latitude}-${city.longitude}`"
              type="button"
              class="city-result"
              @click="applyCity(city)"
            >
              {{ city.label }} ({{ city.latitude.toFixed(2) }}, {{ city.longitude.toFixed(2) }})
            </button>
          </div>

          <button type="submit" class="run-btn" :disabled="isLoading">
            {{ isLoading ? "Analyzing..." : "Run analysis" }}
          </button>
        </form>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <p v-for="warning in warnings" :key="warning" class="warning">{{ warning }}</p>
      </section>

      <section v-if="computedStats" class="panel">
        <h2>Overview</h2>
        <p class="meta">
          {{ computedStats.meta.owner }}/{{ computedStats.meta.repo }} on
          <strong>{{ computedStats.meta.branch }}</strong> from
          {{ computedStats.meta.startDate }} to {{ computedStats.meta.endDate }}.
        </p>
        <p v-if="computedStats.meta.locationLabel" class="meta">Location: {{ computedStats.meta.locationLabel }}</p>

        <div class="split-grid">
          <article class="metric rainy">
            <h3>Rainy commits</h3>
            <p class="big">{{ computedStats.rainyCommits }}</p>
            <p>{{ computedStats.rainyShare.toFixed(1) }}% of total</p>
          </article>
          <article class="metric dry">
            <h3>Dry commits</h3>
            <p class="big">{{ computedStats.dryCommits }}</p>
            <p>{{ computedStats.dryShare.toFixed(1) }}% of total</p>
          </article>
        </div>

        <label class="slider-wrap">
          Rain threshold: <strong>{{ computedStats.threshold.toFixed(1) }} mm/day</strong>
          <input v-model.number="rainThreshold" type="range" min="0" max="20" step="0.5" />
        </label>

        <div class="summary-line">
          <span>{{ computedStats.totalCommits }} commits analyzed</span>
          <span>{{ computedStats.rainyDays }} rainy days</span>
          <span>{{ computedStats.dryDays }} dry days</span>
        </div>
      </section>

      <section v-if="computedStats" class="panel">
        <h2>Monthly trend</h2>
        <div class="month-list">
          <article v-for="row in computedStats.monthlyRows" :key="row.month" class="month-row">
            <div class="month-head">
              <span>{{ row.month }}</span>
              <span>{{ row.total }} commits</span>
            </div>
            <div class="stack-bar" :title="`${row.rainy} rainy commits, ${row.dry} dry commits`">
              <div class="stack-rainy" :style="{ width: `${row.total ? (row.rainy / row.total) * 100 : 0}%` }"></div>
              <div class="stack-dry" :style="{ width: `${row.total ? (row.dry / row.total) * 100 : 0}%` }"></div>
            </div>
          </article>
        </div>
      </section>

      <section v-if="computedStats" class="panel">
        <h2>Day-of-week insights</h2>
        <div class="weekday-grid">
          <article v-for="row in computedStats.weekdayRows" :key="row.name" class="weekday-card">
            <h3>{{ row.name }}</h3>
            <p>{{ row.total }} commits</p>
            <p class="mini">Rainy {{ row.rainy }} | Dry {{ row.dry }}</p>
          </article>
        </div>
        <p class="hint">
          Most active day: <strong>{{ computedStats.strongestDay.name }}</strong>
          ({{ computedStats.strongestDay.total }} commits)
        </p>
      </section>

      <section v-if="computedStats" class="panel verdict-panel">
        <h2>Verdict</h2>
        <p>{{ computedStats.verdict }}</p>
      </section>
    </main>
  </div>
</template>
