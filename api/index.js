const ytdl = require('@distube/ytdl-core');
const { Readable } = require('stream');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { url } = req.body;

  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  try {
    const info = await ytdl.getInfo(url);
    const title = info.videoDetails.title.replace(/[^a-zA-Z0-9 ]/g, '').substring(0, 100);

    const stream = ytdl(url, {
      filter: 'audioonly',
      quality: 'highestaudio',
    });

    const chunks = [];
    for await (const chunk of stream) {
      chunks.push(chunk);
    }
    const buffer = Buffer.concat(chunks);

    const base64Data = buffer.toString('base64');

    return res.status(200).json({
      status: 'completed',
      files: [{
        name: `${title}.webm`,
        size: buffer.length,
        data: base64Data
      }]
    });

  } catch (err) {
    return res.status(400).json({ error: err.message || 'Failed to download' });
  }
};