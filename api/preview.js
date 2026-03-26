const AGE_CODE_MAP = {
  '10': 'AGE_10',
  '20': 'AGE_20',
  '30': 'AGE_30',
  '40': 'AGE_40',
  '50': 'AGE_50',
  '60+': 'AGE_60_UP',
};

const TEMPLATE_PRESETS = {
  brand_general: { intents: ['BRAND', 'GENERAL'], devices: ['PC', 'MOBILE'] },
  device_specific: { intents: ['MIXED'], devices: ['PC', 'MOBILE'] },
  shopping_focus: { intents: ['SHOPPING'], devices: ['MOBILE'] },
};

function parseCsv(raw, fallback = []) {
  if (!raw || typeof raw !== 'string') return fallback;
  const items = raw.split(',').map((v) => v.trim()).filter(Boolean);
  return items.length ? items : fallback;
}

function buildAgeTarget(excludeAges) {
  const excluded = excludeAges.map((a) => AGE_CODE_MAP[a]).filter(Boolean);
  const included = Object.values(AGE_CODE_MAP).filter((code) => !excluded.includes(code));
  return { include: included, exclude: excluded };
}

function buildPreview({ template, categories, genders, regions, excludeAges }) {
  const preset = TEMPLATE_PRESETS[template] || TEMPLATE_PRESETS.brand_general;
  const age = buildAgeTarget(excludeAges);
  const campaigns = [];

  categories.forEach((category) => {
    preset.devices.forEach((device) => {
      preset.intents.forEach((intent) => {
        const campaignName = `${category}_${intent}_${device}`;
        const adgroups = [];
        genders.forEach((gender) => {
          regions.forEach((region) => {
            adgroups.push({
              name: `${campaignName}_${gender}_${region}`,
              targets: { age, gender, region },
            });
          });
        });
        campaigns.push({ campaignName, adgroups });
      });
    });
  });

  const lines = [
    `Template: ${template}`,
    `Campaigns: ${campaigns.length}, AdGroups: ${campaigns.reduce((sum, c) => sum + c.adgroups.length, 0)}`,
  ];
  campaigns.forEach((campaign) => {
    lines.push(`└─ Campaign: ${campaign.campaignName}`);
    campaign.adgroups.forEach((adgroup) => {
      const exAges = adgroup.targets.age.exclude.join(',') || '없음';
      lines.push(`   └─ AdGroup: ${adgroup.name} | gender=${adgroup.targets.gender} | region=${adgroup.targets.region} | exclude_age=${exAges}`);
    });
  });

  return lines.join('\n');
}

module.exports = (req, res) => {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' });
    return;
  }

  const body = req.body || {};
  const template = body.template || 'brand_general';
  const categories = parseCsv(body.categories, ['default']);
  const genders = parseCsv(body.genders, ['ALL']);
  const regions = parseCsv(body.regions, ['전국']);
  const excludeAges = parseCsv(body.excludeAges, []);

  const tree = buildPreview({ template, categories, genders, regions, excludeAges });
  res.status(200).json({ tree });
};
