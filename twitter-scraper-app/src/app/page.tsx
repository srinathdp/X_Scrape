import Link from 'next/link';

export default function Home() {
  const cards = [
    { title: 'Search Tweets', desc: 'Search for tweets by keyword or phrase. Filter by latest, top, or media tweets.', href: '/search' },
    { title: 'Hashtag Tweets', desc: 'Search for tweets by hashtag. Find trending topics and conversations.', href: '/hashtag' },
    { title: 'User Tweets', desc: 'Retrieve tweets from specific users. Get tweets, replies, media, or likes.', href: '/user' },
    { title: 'Date Range Tweets', desc: 'Find tweets from a specific time period. Filter by date range.', href: '/date-range' },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-white">X Scraper Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((c) => (
          <div key={c.title} className="bg-gray-900 border border-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-4 border-b border-gray-800">
              <h2 className="text-xl font-semibold text-white">{c.title}</h2>
            </div>
            <div className="p-6">
              <p className="text-gray-300 mb-4">{c.desc}</p>
              <Link href={c.href} className="block text-center py-2 px-4 bg-[#1da1f2] text-white font-semibold rounded-full hover:bg-[#1484b8] transition btn-action">
                Get Started
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 p-6 bg-gray-900 border border-gray-800 rounded-lg">
        <h2 className="text-2xl font-bold mb-4 text-white">View Scraping Jobs</h2>
        <p className="text-gray-300 mb-4">View all scraping jobs and their results. Monitor progress and browse collected tweets.</p>
        <Link href="/jobs" className="inline-block py-2 px-6 bg-[#1da1f2] text-white font-semibold rounded-full hover:bg-[#1484b8] transition btn-action">
          View Jobs
        </Link>
      </div>
    </div>
  );
}
