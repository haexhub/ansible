// ./directus-sync.config.js
module.exports = {
  //extends: ['./directus-sync.config.base.js'],
  debug: true,
  directusUrl: '$directusUrl',
  //directusToken: 'my-directus-token',
  directusEmail: '$directusEmail', // ignored if directusToken is provided
  directusPassword: '$directusPassword', // ignored if directusToken is provided
  //directusConfig: {
  //  clientOptions: {}, // see https://docs.directus.io/guides/sdk/getting-started.html#polyfilling
  //  restConfig: {}, // see https://docs.directus.io/packages/@directus/sdk/rest/interfaces/RestConfig.html
  //},
  dumpPath: './directus-config',
  //collectionsPath: 'collections',
  //preserveIds: '*', // can be '*' or 'all' to preserve all ids, or an array of collections
  snapshotPath: 'snapshot',
  snapshot: true,
  split: true,
  specsPath: 'specs',
  specs: true,
};
