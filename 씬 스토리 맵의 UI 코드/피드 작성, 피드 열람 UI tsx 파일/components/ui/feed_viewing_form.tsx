"use client";

import { useState, useRef, useEffect } from "react";
import { Heart, MessageCircle, Share2, Bookmark, MoreHorizontal, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface FeedImage {
  id: string;
  url: string;
  alt: string;
}

interface FeedAuthor {
  name: string;
  username: string;
  avatar: string;
  timeAgo: string;
}

interface FeedEngagement {
  likes: number;
  comments: number;
  shares: number;
  isLiked: boolean;
  isBookmarked: boolean;
}

interface FeedPost {
  id: string;
  author: FeedAuthor;
  images: FeedImage[];
  caption: string;
  engagement: FeedEngagement;
}

interface ImageCarouselProps {
  images: FeedImage[];
  className?: string;
}

function ImageCarousel({ images, className }: ImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToImage = (index: number) => {
    if (scrollRef.current) {
      const imageWidth = scrollRef.current.clientWidth;
      scrollRef.current.scrollTo({
        left: index * imageWidth,
        behavior: 'smooth'
      });
    }
    setCurrentIndex(index);
  };

  const nextImage = () => {
    const nextIndex = (currentIndex + 1) % images.length;
    scrollToImage(nextIndex);
  };

  const prevImage = () => {
    const prevIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
    scrollToImage(prevIndex);
  };

  const handleScroll = () => {
    if (scrollRef.current) {
      const imageWidth = scrollRef.current.clientWidth;
      const scrollLeft = scrollRef.current.scrollLeft;
      const index = Math.round(scrollLeft / imageWidth);
      setCurrentIndex(index);
    }
  };

  if (images.length === 0) return null;

  return (
    <div className={cn("relative w-full", className)}>
      <div
        ref={scrollRef}
        className="flex overflow-x-auto scrollbar-hide snap-x snap-mandatory"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        onScroll={handleScroll}
      >
        {images.map((image, index) => (
          <div key={image.id} className="w-full flex-shrink-0 snap-start">
            <img
              src={image.url}
              alt={image.alt}
              className="w-full h-80 object-cover"
            />
          </div>
        ))}
      </div>

      {images.length > 1 && (
        <>
          <button
            onClick={prevImage}
            className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-2 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={nextImage}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-2 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex space-x-1">
            {images.map((_, index) => (
              <button
                key={index}
                onClick={() => scrollToImage(index)}
                className={cn(
                  "w-2 h-2 rounded-full transition-colors",
                  index === currentIndex ? "bg-white" : "bg-white/50"
                )}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

interface FeedCardProps {
  post: FeedPost;
  onLike?: (postId: string) => void;
  onComment?: (postId: string) => void;
  onShare?: (postId: string) => void;
  onBookmark?: (postId: string) => void;
  onMore?: (postId: string) => void;
  className?: string;
}

function FeedCard({
  post,
  onLike,
  onComment,
  onShare,
  onBookmark,
  onMore,
  className
}: FeedCardProps) {
  const [isLiked, setIsLiked] = useState(post.engagement.isLiked);
  const [isBookmarked, setIsBookmarked] = useState(post.engagement.isBookmarked);
  const [likes, setLikes] = useState(post.engagement.likes);

  const handleLike = () => {
    setIsLiked(!isLiked);
    setLikes(prev => isLiked ? prev - 1 : prev + 1);
    onLike?.(post.id);
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    onBookmark?.(post.id);
  };

  return (
    <div
      className={cn(
        "w-full max-w-lg mx-auto",
        "bg-background border border-border rounded-lg overflow-hidden",
        "shadow-sm",
        className
      )}
    >
      {/* Author Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <img
            src={post.author.avatar}
            alt={post.author.name}
            className="w-10 h-10 rounded-full object-cover"
          />
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              {post.author.name}
            </h3>
            <p className="text-xs text-muted-foreground">
              @{post.author.username} · {post.author.timeAgo}
            </p>
          </div>
        </div>
        <button
          onClick={() => onMore?.(post.id)}
          className="p-2 hover:bg-muted rounded-full transition-colors"
        >
          <MoreHorizontal className="w-5 h-5 text-muted-foreground" />
        </button>
      </div>

      {/* Image Carousel */}
      <ImageCarousel images={post.images} />

      {/* Engagement Actions */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4">
            <button
              onClick={handleLike}
              className={cn(
                "flex items-center gap-2 text-sm transition-colors",
                isLiked
                  ? "text-red-500"
                  : "text-muted-foreground hover:text-red-500"
              )}
            >
              <Heart
                className={cn(
                  "w-6 h-6 transition-all",
                  isLiked && "fill-current scale-110"
                )}
              />
              <span>{likes}</span>
            </button>
            <button
              onClick={() => onComment?.(post.id)}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-blue-500 transition-colors"
            >
              <MessageCircle className="w-6 h-6" />
              <span>{post.engagement.comments}</span>
            </button>
            <button
              onClick={() => onShare?.(post.id)}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-green-500 transition-colors"
            >
              <Share2 className="w-6 h-6" />
              <span>{post.engagement.shares}</span>
            </button>
          </div>
          <button
            onClick={handleBookmark}
            className={cn(
              "p-2 rounded-full transition-all",
              isBookmarked
                ? "text-yellow-500 bg-yellow-50 dark:bg-yellow-500/10"
                : "text-muted-foreground hover:bg-muted"
            )}
          >
            <Bookmark
              className={cn(
                "w-5 h-5 transition-transform",
                isBookmarked && "fill-current scale-110"
              )}
            />
          </button>
        </div>

        {/* Caption */}
        <div className="text-sm text-foreground">
          <span className="font-semibold">{post.author.username}</span>{" "}
          {post.caption}
        </div>
      </div>
    </div>
  );
}

interface FeedViewerProps {
  posts?: FeedPost[];
  className?: string;
}

function FeedViewer({ posts = [], className }: FeedViewerProps) {
  const handleAction = (postId: string, action: string) => {
    console.log(`Post ${postId}: ${action}`);
  };

  return (
    <div className={cn("w-full max-w-2xl mx-auto", className)}>
      <div className="space-y-6">
        {posts.map((post) => (
          <FeedCard
            key={post.id}
            post={post}
            onLike={(id) => handleAction(id, 'liked')}
            onComment={(id) => handleAction(id, 'commented')}
            onShare={(id) => handleAction(id, 'shared')}
            onBookmark={(id) => handleAction(id, 'bookmarked')}
            onMore={(id) => handleAction(id, 'more')}
          />
        ))}
      </div>
    </div>
  );
}

export default function FeedViewerDemo() {
  const samplePosts: FeedPost[] = [
    {
      id: "1",
      author: {
        name: "Sarah Johnson",
        username: "sarahj_photo",
        avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face",
        timeAgo: "2h ago"
      },
      images: [
        {
          id: "img1",
          url: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop",
          alt: "Mountain landscape"
        },
        {
          id: "img2",
          url: "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=600&h=400&fit=crop",
          alt: "Forest path"
        },
        {
          id: "img3",
          url: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&h=400&fit=crop",
          alt: "River valley"
        }
      ],
      caption: "Amazing hiking trip through the mountains! The views were absolutely breathtaking. Can't wait to go back next weekend! 🏔️ #hiking #nature #adventure",
      engagement: {
        likes: 234,
        comments: 18,
        shares: 12,
        isLiked: false,
        isBookmarked: false
      }
    },
    {
      id: "2",
      author: {
        name: "Alex Chen",
        username: "alexc_food",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
        timeAgo: "4h ago"
      },
      images: [
        {
          id: "img4",
          url: "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=600&h=400&fit=crop",
          alt: "Delicious pizza"
        },
        {
          id: "img5",
          url: "https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=600&h=400&fit=crop",
          alt: "Fresh salad"
        }
      ],
      caption: "Tried this new Italian restaurant downtown. The pizza was incredible and the salad was so fresh! Highly recommend checking it out. 🍕🥗",
      engagement: {
        likes: 156,
        comments: 23,
        shares: 8,
        isLiked: true,
        isBookmarked: true
      }
    },
    {
      id: "3",
      author: {
        name: "Maya Patel",
        username: "maya_travels",
        avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
        timeAgo: "1d ago"
      },
      images: [
        {
          id: "img6",
          url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&h=400&fit=crop",
          alt: "Tropical beach"
        }
      ],
      caption: "Paradise found! 🏝️ This beach in Maldives is everything I dreamed of and more. Crystal clear waters and the softest sand. #maldives #beach #paradise #vacation",
      engagement: {
        likes: 892,
        comments: 67,
        shares: 45,
        isLiked: false,
        isBookmarked: false
      }
    }
  ];

  return (
    <div className="min-h-screen bg-background p-4">
      <FeedViewer posts={samplePosts} />
    </div>
  );
}
